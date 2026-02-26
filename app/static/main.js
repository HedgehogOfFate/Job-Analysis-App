let locationChartInstance = null;
let skillsChartInstance = null;
let workTypeChartInstance = null;
let experienceChartInstance = null;
let skillsCategoryChartInstance = null;
let salaryLocationChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM loaded");

    const form = document.getElementById("searchForm");

    if (!form) {
        console.error("Form not found!");
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const what = document.getElementById("what").value;
        const where = document.getElementById("where").value;
        const country = document.getElementById("country").value;

        if (!what) {
            alert("Please enter a search term");
            return;
        }

        if (!country) {
            alert("Please select a country");
            return;
        }

        const loadingEl = document.getElementById("loading");
        const progressBar = document.getElementById("progressBar");
        const progressText = document.getElementById("progressText");

        if (loadingEl) {
            loadingEl.classList.add("active");
        }

        let progress = 0;
        const progressInterval = setInterval(() => {
            if (progress < 90) {
                progress += Math.random() * 8;
                progress = Math.min(progress, 90);
                if (progressBar) progressBar.style.width = progress + "%";
                if (progressText) {
                    if (progress < 30) {
                        progressText.textContent = "Connecting to job API...";
                    } else if (progress < 60) {
                        progressText.textContent = "Fetching job listings...";
                    } else {
                        progressText.textContent = "Analyzing results...";
                    }
                }
            }
        }, 300);

        try {
            const response = await fetch(`/api/search?what=${encodeURIComponent(what)}&where=${encodeURIComponent(where)}&country=${encodeURIComponent(country)}`);

            clearInterval(progressInterval);
            if (progressBar) progressBar.style.width = "100%";
            if (progressText) progressText.textContent = "Done!";

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            console.log("Received data:", data);

            updateSummary(data);
            renderLocationChart(data.jobs_by_location || {});
            renderSkillsChart(data.top_skills || []);
            renderWorkTypeChart(data.work_type_breakdown || {});
            renderExperienceChart(data.experience_breakdown || {});
            renderSkillsCategoryChart(data.skills_by_category || {});
            renderSalaryLocationChart(data.salary_by_location || {});

            showResultsSections();

        } catch (error) {
            clearInterval(progressInterval);
            alert(`Error fetching data: ${error.message}`);
            console.error("Fetch error:", error);
        } finally {
            setTimeout(() => {
                if (loadingEl) {
                    loadingEl.classList.remove("active");
                }
                if (progressBar) progressBar.style.width = "0%";
            }, 500);
        }
    });
});

function showResultsSections() {
    const sections = ["summary", "insightsSection", "chartsSection", "extraChartsSection", "exportSection"];
    sections.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove("hidden");
    });
}

function updateSummary(data) {
    const totalJobsEl = document.getElementById("totalJobs");
    const avgSalaryEl = document.getElementById("avgSalary");
    const salaryRangeEl = document.getElementById("salaryRange");

    if (!totalJobsEl || !avgSalaryEl || !salaryRangeEl) {
        console.error("Some elements not found!");
        return;
    }

    totalJobsEl.textContent = data.total_jobs || 0;

    if (data.salary_stats && data.salary_stats.count > 0) {
        const { avg, min, max } = data.salary_stats;
        const currencySymbol = detectCurrency();

        avgSalaryEl.textContent = `${currencySymbol}${Math.round(avg).toLocaleString()} /year`;
        salaryRangeEl.textContent = `${currencySymbol}${Math.round(min).toLocaleString()} - ${currencySymbol}${Math.round(max).toLocaleString()}`;
    } else {
        avgSalaryEl.textContent = "N/A";
        salaryRangeEl.textContent = "No data";
    }
}

function detectCurrency() {
    const country = document.getElementById("country")?.value;

    const currencyMap = {
        'gb': '\u00a3',
        'us': '$',
        'ca': '$',
        'au': '$',
        'nz': '$',
        'sg': '$',
        'de': '\u20ac',
        'fr': '\u20ac',
        'it': '\u20ac',
        'nl': '\u20ac',
        'at': '\u20ac',
        'pl': 'z\u0142',
        'in': '\u20b9',
        'br': 'R$',
        'za': 'R'
    };

    return currencyMap[country] || '\u20ac';
}

function renderLocationChart(locationData) {
    if (!locationData || Object.keys(locationData).length === 0) {
        return;
    }

    const canvas = document.getElementById("locationChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (locationChartInstance) {
        locationChartInstance.destroy();
    }

    const entries = Object.entries(locationData).slice(0, 20);
    const labels = entries.map(e => e[0]);
    const values = entries.map(e => e[1]);

    locationChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Number of Jobs",
                data: values,
                backgroundColor: "rgba(37, 99, 235, 0.7)",
                borderColor: "rgba(37, 99, 235, 1)",
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: 'rgba(0,0,0,0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderSkillsChart(skillsArray) {
    if (!skillsArray || skillsArray.length === 0) return;

    const canvas = document.getElementById("skillsChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (skillsChartInstance) {
        skillsChartInstance.destroy();
    }

    const labels = skillsArray.map(item => item[0]);
    const values = skillsArray.map(item => item[1]);

    skillsChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    "rgba(102, 126, 234, 0.8)",
                    "rgba(118, 75, 162, 0.8)",
                    "rgba(255, 99, 132, 0.8)",
                    "rgba(255, 159, 64, 0.8)",
                    "rgba(75, 192, 192, 0.8)",
                    "rgba(153, 102, 255, 0.8)",
                    "rgba(255, 205, 86, 0.8)",
                    "rgba(201, 203, 207, 0.8)",
                    "rgba(54, 162, 235, 0.8)"
                ],
                borderColor: "white",
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

function renderWorkTypeChart(workTypeData) {
    if (!workTypeData) return;

    const canvas = document.getElementById("workTypeChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (workTypeChartInstance) {
        workTypeChartInstance.destroy();
    }

    const labelMap = {
        remote: "Remote",
        hybrid: "Hybrid",
        onsite: "On-site",
        unspecified: "Unspecified"
    };

    const colorMap = {
        remote: "rgba(34, 197, 94, 0.8)",
        hybrid: "rgba(59, 130, 246, 0.8)",
        onsite: "rgba(249, 115, 22, 0.8)",
        unspecified: "rgba(156, 163, 175, 0.8)"
    };

    const labels = [];
    const values = [];
    const colors = [];

    for (const [key, count] of Object.entries(workTypeData)) {
        if (count > 0) {
            labels.push(labelMap[key] || key);
            values.push(count);
            colors.push(colorMap[key] || "rgba(156, 163, 175, 0.8)");
        }
    }

    if (values.length === 0) return;

    workTypeChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: "white",
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 12,
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function renderExperienceChart(experienceData) {
    if (!experienceData) return;

    const canvas = document.getElementById("experienceChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (experienceChartInstance) {
        experienceChartInstance.destroy();
    }

    const labelMap = {
        entry_level: "Entry Level",
        mid_level: "Mid Level",
        senior: "Senior",
        unspecified: "Unspecified"
    };

    const colorMap = {
        entry_level: "rgba(34, 197, 94, 0.7)",
        mid_level: "rgba(59, 130, 246, 0.7)",
        senior: "rgba(168, 85, 247, 0.7)",
        unspecified: "rgba(156, 163, 175, 0.7)"
    };

    const labels = [];
    const values = [];
    const colors = [];

    for (const [key, count] of Object.entries(experienceData)) {
        labels.push(labelMap[key] || key);
        values.push(count);
        colors.push(colorMap[key] || "rgba(156, 163, 175, 0.7)");
    }

    experienceChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Job Count",
                data: values,
                backgroundColor: colors,
                borderRadius: 8,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: 'rgba(0,0,0,0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderSkillsCategoryChart(categoryData) {
    if (!categoryData || Object.keys(categoryData).length === 0) return;

    const canvas = document.getElementById("skillsCategoryChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (skillsCategoryChartInstance) {
        skillsCategoryChartInstance.destroy();
    }

    const categories = [];
    const totals = [];

    const sorted = Object.entries(categoryData)
        .map(([cat, skills]) => [cat, skills.reduce((sum, s) => sum + s[1], 0)])
        .sort((a, b) => b[1] - a[1]);

    for (const [cat, total] of sorted) {
        categories.push(cat);
        totals.push(total);
    }

    const catColors = [
        "rgba(102, 126, 234, 0.7)",
        "rgba(118, 75, 162, 0.7)",
        "rgba(255, 99, 132, 0.7)",
        "rgba(255, 159, 64, 0.7)",
        "rgba(75, 192, 192, 0.7)",
        "rgba(153, 102, 255, 0.7)",
        "rgba(255, 205, 86, 0.7)",
        "rgba(54, 162, 235, 0.7)"
    ];

    skillsCategoryChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: categories,
            datasets: [{
                label: "Total Mentions",
                data: totals,
                backgroundColor: catColors.slice(0, categories.length),
                borderRadius: 8,
                borderWidth: 0
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: 'rgba(0,0,0,0.05)' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderSalaryLocationChart(salaryLocData) {
    if (!salaryLocData || Object.keys(salaryLocData).length === 0) return;

    const canvas = document.getElementById("salaryLocationChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (salaryLocationChartInstance) {
        salaryLocationChartInstance.destroy();
    }

    const currencySymbol = detectCurrency();

    const sorted = Object.entries(salaryLocData)
        .sort((a, b) => b[1].avg - a[1].avg);

    const labels = sorted.map(([loc]) => loc);
    const avgValues = sorted.map(([, stats]) => Math.round(stats.avg));

    salaryLocationChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Average Salary",
                data: avgValues,
                backgroundColor: "rgba(34, 197, 94, 0.7)",
                borderColor: "rgba(34, 197, 94, 1)",
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${currencySymbol}${context.parsed.x.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return currencySymbol + value.toLocaleString();
                        }
                    },
                    grid: { color: 'rgba(0,0,0,0.05)' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

function downloadData(format) {
    window.location.href = `/api/export/${format}`;
}

function downloadChart(chartType) {
    const summaryEl = document.getElementById("summary");
    if (!summaryEl || summaryEl.classList.contains("hidden")) {
        alert("Please perform a search first before downloading charts.");
        return;
    }

    window.location.href = `/api/export/chart/${chartType}`;
}

window.downloadData = downloadData;
window.downloadChart = downloadChart;
