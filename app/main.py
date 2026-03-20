from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import logging
from typing import Optional
from .clients.adzuna_client import AdzunaClient
from .analysis.skill_extractor import SkillExtractor
from .analysis.analyzer import JobAnalyzer
from .exporter.exporter import DataExporter, ChartExporter
from .cache import cache, make_search_cache_key
from . import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Labor Market Analysis System")

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory="app/static"), name="static")

try:
    adzuna = AdzunaClient(
        app_id=config.ADZUNA_APP_ID,
        app_key=config.ADZUNA_APP_KEY,
        results_per_page=config.ADZUNA_RESULTS_PER_PAGE
    )
    skill_extractor = SkillExtractor()
    analyzer = JobAnalyzer(skill_extractor=skill_extractor)
    logger.info("Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize application: {str(e)}")
    raise

last_search_result = {}
last_search_country = ""


@app.on_event("startup")
async def startup_event():
    await cache.connect()


@app.on_event("shutdown")
async def shutdown_event():
    await adzuna.close()
    await cache.close()
    logger.info("Application shutdown: closed HTTP client and Redis connection")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "error_type": type(exc).__name__
        }
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error serving index page: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load the application page"
        )


@app.get("/api/search")
async def api_search(
        what: str = "",
        where: str = "",
        country: Optional[str] = None,
        fetch_all: bool = True
):
    global last_search_result, last_search_country

    if not config.ADZUNA_APP_ID or not config.ADZUNA_APP_KEY:
        logger.error("Adzuna credentials not configured")
        raise HTTPException(
            status_code=500,
            detail="Adzuna credentials not configured on server. Please contact administrator."
        )

    if not country:
        logger.warning("Search attempted without country parameter")
        raise HTTPException(
            status_code=400,
            detail="Country parameter is required."
        )

    if not what:
        logger.warning("Search attempted without search term")
        raise HTTPException(
            status_code=400,
            detail="Search term (what) is required."
        )

    valid_countries = ['gb', 'us', 'de', 'fr', 'ca', 'au', 'nl', 'it', 'pl', 'in', 'br', 'at', 'nz', 'sg', 'za']
    if country.lower() not in valid_countries:
        logger.warning(f"Invalid country code: {country}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid country code. Must be one of: {', '.join(valid_countries)}"
        )

    try:
        logger.info(f"Starting job search: what={what}, where={where}, country={country}, fetch_all={fetch_all}")

        # --- Cache check ---
        cache_key = make_search_cache_key(what, where, country)
        cached_result = await cache.get(cache_key)
        if cached_result:
            last_search_result = cached_result
            last_search_country = country.lower()
            logger.info(f"Returning cached result for key: {cache_key}")
            return JSONResponse(content=cached_result)

        # --- Cache miss: fetch from Adzuna ---
        if fetch_all:
            jobs = await adzuna.search_all_jobs(
                what=what,
                country=country,
                where=where,
                max_pages=config.ADZUNA_MAX_PAGES
            )
        else:
            jobs = await adzuna.search_jobs(
                what=what,
                country=country,
                where=where,
                page=1
            )

        if not jobs:
            logger.warning(f"No jobs found for search: what={what}, where={where}, country={country}")
            return JSONResponse(
                status_code=200,
                content={
                    "total_jobs": 0,
                    "jobs_by_location": {},
                    "top_skills": [],
                    "skills_by_category": {},
                    "salary_stats": {
                        "count": 0,
                        "avg": None,
                        "min": None,
                        "max": None,
                        "period": "annual",
                        "breakdown": {"hourly": 0, "monthly": 0, "annual": 0, "predicted": 0}
                    },
                    "work_type_breakdown": {"remote": 0, "hybrid": 0, "onsite": 0, "unspecified": 0},
                    "experience_breakdown": {"entry_level": 0, "mid_level": 0, "senior": 0, "unspecified": 0},
                    "salary_by_location": {},
                    "message": "No jobs found matching your search criteria. Try broadening your search terms."
                }
            )

        logger.info(f"Successfully fetched {len(jobs)} jobs")

        try:
            result = analyzer.analyze(jobs, country=country.lower())
            last_search_result = result
            last_search_country = country.lower()
            logger.info(f"Successfully analyzed {result['total_jobs']} jobs")
        except Exception as e:
            logger.error(f"Error analyzing jobs: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze job data. Please try again."
            )

        # --- Store result in cache ---
        await cache.set(cache_key, result)

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during job search: {str(e)}", exc_info=True)

        error_message = "An error occurred while searching for jobs."

        if "timeout" in str(e).lower():
            error_message = "The search request timed out. Please try again with a more specific search."
        elif "connection" in str(e).lower():
            error_message = "Failed to connect to the job data service. Please check your internet connection and try again."
        elif "rate limit" in str(e).lower():
            error_message = "Too many requests. Please wait a moment and try again."

        raise HTTPException(
            status_code=500,
            detail=error_message
        )


@app.get("/api/search/cache/clear")
async def clear_search_cache(what: str = "", where: str = "", country: str = ""):
    if not what or not country:
        raise HTTPException(status_code=400, detail="'what' and 'country' parameters are required.")
    key = make_search_cache_key(what, where, country)
    deleted = await cache.delete(key)
    if deleted:
        return JSONResponse(content={"message": f"Cache cleared for key: {key}"})
    raise HTTPException(status_code=404, detail="Key not found in cache or Redis unavailable.")


@app.get("/health")
async def health_check():
    try:
        health_status = {
            "status": "healthy",
            "adzuna_configured": bool(config.ADZUNA_APP_ID and config.ADZUNA_APP_KEY),
            "last_search_available": bool(last_search_result),
            "redis_available": cache.available,
        }
        return JSONResponse(content=health_status)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/api/export/csv")
async def export_csv():
    if not last_search_result:
        logger.warning("CSV export attempted without search results")
        raise HTTPException(
            status_code=400,
            detail="No search results available. Please perform a search first."
        )

    try:
        logger.info("Generating CSV export")
        csv_data = DataExporter.to_csv(last_search_result)

        if not csv_data:
            raise ValueError("Generated CSV data is empty")

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=job_analysis.csv"}
        )
    except Exception as e:
        logger.error(f"Error generating CSV export: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate CSV file. Please try again."
        )


@app.get("/api/export/xlsx")
async def export_xlsx():
    if not last_search_result:
        logger.warning("Excel export attempted without search results")
        raise HTTPException(
            status_code=400,
            detail="No search results available. Please perform a search first."
        )

    try:
        logger.info("Generating Excel export")
        xlsx_data = DataExporter.to_xlsx(last_search_result)

        if not xlsx_data:
            raise ValueError("Generated Excel data is empty")

        return Response(
            content=xlsx_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=job_analysis.xlsx"}
        )
    except Exception as e:
        logger.error(f"Error generating Excel export: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate Excel file. Please try again."
        )


@app.get("/api/export/chart/location")
async def export_location_chart():
    if not last_search_result:
        logger.warning("Location chart export attempted without search results")
        raise HTTPException(
            status_code=400,
            detail="No search results available. Please perform a search first."
        )

    try:
        location_data = last_search_result.get('jobs_by_location', {})

        if not location_data:
            raise HTTPException(
                status_code=400,
                detail="No location data available. Try searching with a city or region specified."
            )

        if sum(location_data.values()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Location data is empty. Please perform a search with results first."
            )

        chart_data = ChartExporter.create_location_chart(location_data)
        if not chart_data:
            raise ValueError("Generated chart data is empty")

        return Response(
            content=chart_data,
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=location_chart.png"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating location chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate location chart. Please try again.")


@app.get("/api/export/chart/skills")
async def export_skills_chart():
    if not last_search_result:
        raise HTTPException(status_code=400, detail="No search results available. Please perform a search first.")

    try:
        skills_data = last_search_result.get('top_skills')
        if not skills_data:
            raise HTTPException(status_code=400, detail="No skills data available. Please perform a search first.")

        chart_data = ChartExporter.create_skills_chart(skills_data)
        if not chart_data:
            raise ValueError("Generated chart data is empty")

        return Response(
            content=chart_data,
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=skills_chart.png"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating skills chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate skills chart. Please try again.")


@app.get("/api/export/chart/work-type")
async def export_work_type_chart():
    if not last_search_result:
        raise HTTPException(status_code=400, detail="No search results available. Please perform a search first.")

    try:
        data = last_search_result.get('work_type_breakdown', {})
        if not data or all(v == 0 for v in data.values()):
            raise HTTPException(status_code=400, detail="No work type data available.")

        chart_data = ChartExporter.create_work_type_chart(data)
        return Response(content=chart_data, media_type="image/png",
                        headers={"Content-Disposition": "attachment; filename=work_type_chart.png"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating work type chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate work type chart.")


@app.get("/api/export/chart/experience")
async def export_experience_chart():
    if not last_search_result:
        raise HTTPException(status_code=400, detail="No search results available. Please perform a search first.")

    try:
        data = last_search_result.get('experience_breakdown', {})
        if not data or all(v == 0 for v in data.values()):
            raise HTTPException(status_code=400, detail="No experience level data available.")

        chart_data = ChartExporter.create_experience_chart(data)
        return Response(content=chart_data, media_type="image/png",
                        headers={"Content-Disposition": "attachment; filename=experience_chart.png"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating experience chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate experience chart.")


@app.get("/api/export/chart/skills-category")
async def export_skills_category_chart():
    if not last_search_result:
        raise HTTPException(status_code=400, detail="No search results available. Please perform a search first.")

    try:
        data = last_search_result.get('skills_by_category', {})
        if not data:
            raise HTTPException(status_code=400, detail="No skills category data available.")

        chart_data = ChartExporter.create_skills_category_chart(data)
        return Response(content=chart_data, media_type="image/png",
                        headers={"Content-Disposition": "attachment; filename=skills_category_chart.png"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating skills category chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate skills category chart.")


@app.get("/api/export/chart/salary-location")
async def export_salary_location_chart():
    if not last_search_result:
        raise HTTPException(status_code=400, detail="No search results available. Please perform a search first.")

    try:
        data = last_search_result.get('salary_by_location', {})
        if not data:
            raise HTTPException(status_code=400, detail="No salary by location data available.")

        currency = DataExporter.get_currency_symbol(last_search_country) if last_search_country else '€'
        chart_data = ChartExporter.create_salary_location_chart(data, currency=currency)
        return Response(content=chart_data, media_type="image/png",
                        headers={"Content-Disposition": "attachment; filename=salary_location_chart.png"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating salary location chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate salary location chart.")