document.addEventListener("DOMContentLoaded", function () {
    console.log("📌 Document fully loaded!");

    // Fetch and display subjects
    function loadSubjects() {
        let subjectsContainer = document.getElementById("subjects-container");
        if (!subjectsContainer) return;

        fetch('/get_subjects')
            .then(response => response.json())
            .then(data => {
                subjectsContainer.innerHTML = "";
                data.subjects.forEach(subject => {
                    let card = document.createElement("div");
                    card.classList.add("col-md-3", "mb-3");
                    card.innerHTML = `
                        <div class="card text-center p-3">
                            <h5>${subject.name}</h5>
                            <button class="btn btn-primary view-quizzes" data-subject="${subject.id}">
                                View Quizzes
                            </button>
                        </div>
                    `;
                    subjectsContainer.appendChild(card);
                });

                document.querySelectorAll(".view-quizzes").forEach(button => {
                    button.addEventListener("click", function () {
                        let subjectId = this.getAttribute("data-subject");
                        window.location.href = `/quizzes/${subjectId}`;
                    });
                });
            })
            .catch(error => console.error("❌ Error fetching subjects:", error));
    }

    // Fetch and display quizzes
    function loadQuizzes() {
        let quizTable = document.getElementById("quiz-table-body");
        if (!quizTable) return;

        fetch('/get_quizzes')
            .then(response => response.json())
            .then(data => {
                quizTable.innerHTML = "";
                data.quizzes.forEach(quiz => {
                    let row = `<tr>
                        <td>${quiz.id}</td>
                        <td>${quiz.chapter_id}</td>
                        <td>${quiz.date_of_quiz}</td>
                        <td>${quiz.time_duration}</td>
                        <td>${quiz.remarks ? quiz.remarks : 'N/A'}</td>
                        <td><button class="btn btn-success start-quiz" data-id="${quiz.id}">Start</button></td>
                    </tr>`;
                    quizTable.innerHTML += row;
                });

                document.querySelectorAll(".start-quiz").forEach(button => {
                    button.addEventListener("click", function () {
                        let quizId = this.getAttribute("data-id");
                        window.location.href = `/start_quiz/${quizId}`;
                    });
                });
            })
            .catch(error => console.error("❌ Error fetching quizzes:", error));
    }

    let quizzesChart = null;
    let answersChart = null;

    function createChart(chartId, chartType, chartData, chartOptions) {
        let chartElement = document.getElementById(chartId);
        if (!chartElement) return null;

        let existingChart = Chart.getChart(chartElement);
        if (existingChart) {
            console.log(`🛠 Destroying existing chart: ${chartId}`);
            existingChart.destroy();
        }

        return new Chart(chartElement.getContext("2d"), {
            type: chartType,
            data: chartData,
            options: chartOptions
        });
    }

    function loadCharts() {
        console.log("🔄 Loading charts...");
    
        fetch('/get_summary_data')
            .then(response => response.json())
            .then(data => {
                console.log("📊 Chart Data:", data);
    
                if (!data.subjects.length) {
                    console.warn("⚠️ No subjects available, skipping chart rendering.");
                    return;
                }
    
                // Debugging: Check correct & incorrect answers count
                console.log("✅ Correct Answers:", data.correct_answers);
                console.log("❌ Incorrect Answers:", data.incorrect_answers);
    
                // Fix: Ensure correct answer count is properly displayed
                let totalAnswers = data.correct_answers + data.incorrect_answers;
                if (totalAnswers === 0) {
                    console.warn("⚠️ No quiz data available for answers chart.");
                    return;
                }
    
                // Render Bar Chart for Quizzes Attempted per Subject
                quizzesChart = createChart("quizzesChart", "bar", {
                    labels: data.subjects,
                    datasets: [{
                        label: "Quizzes Attempted",
                        data: data.quizzes_attempted,
                        backgroundColor: "rgba(75, 192, 192, 0.2)",
                        borderColor: "rgba(75, 192, 192, 1)",
                        borderWidth: 1
                    }]
                }, {
                    responsive: true,
                    maintainAspectRatio: false
                });
    
                // Render Pie Chart for Correct vs Incorrect Answers
                answersChart = createChart("answersChart", "pie", {
                    labels: ["Correct Answers", "Incorrect Answers"],
                    datasets: [{
                        data: [data.correct_answers, data.incorrect_answers], 
                        backgroundColor: ["#4CAF50", "#FF5722"]
                    }]
                }, {
                    responsive: true,
                    maintainAspectRatio: false
                });
    
                console.log("✅ Charts loaded successfully!");
            })
            .catch(error => console.error("❌ Error fetching summary data:", error));
    }
    
    

    // Ensure charts only initialize when the Summary Charts tab is opened
    let chartsTab = document.querySelector("#charts-tab");
    if (chartsTab) {
        chartsTab.addEventListener("shown.bs.tab", function () {
            console.log("📊 Summary Charts tab opened - Initializing charts...");
            setTimeout(() => {
                let chartContainer = document.getElementById("summaryCharts");
                if (chartContainer) {
                    chartContainer.style.display = "block";
                    chartContainer.style.height = "auto";
                }
                loadCharts();
            }, 300);
        });

        // Force Chart.js to redraw properly when resizing window
        window.addEventListener("resize", () => {
            if (chartsTab.classList.contains("active")) {
                loadCharts();
            }
        });
    }

    // Sidebar toggle logic
    let sidebar = document.getElementById('sidebar');
    let main = document.querySelector('main');

    if (sidebar) {
        sidebar.addEventListener('hidden.bs.offcanvas', () => {
            if (main) main.classList.add('sidebar-collapsed');
        });

        sidebar.addEventListener('shown.bs.offcanvas', () => {
            if (main) main.classList.remove('sidebar-collapsed');
        });
    }

    // Initialize Bootstrap dropdowns properly
    document.querySelectorAll('.dropdown-toggle').forEach(dropdown => {
        new bootstrap.Dropdown(dropdown);
    });

    document.addEventListener("DOMContentLoaded", function () {
        let dropdowns = document.querySelectorAll('.dropdown-toggle');
        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('click', function (event) {
                event.preventDefault();
                let bsDropdown = new bootstrap.Dropdown(dropdown);
                bsDropdown.toggle();
            });
        });
    });

    // Load all necessary components
    loadSubjects();
    loadQuizzes();
});
