function updateLeaderboard(selectedSubcategory) {
    var runsData = JSON.parse(document.getElementById("runs-data").textContent);
    var runs = runsData;

    var leaderboardTable = document.getElementById("leaderboard-table");
    var leaderboardBody = leaderboardTable.getElementsByTagName("tbody")[0];
    leaderboardBody.innerHTML = '';

    var filteredRuns = runs.filter(function(run) {
        return run.subcategory === selectedSubcategory;
    });

    filteredRuns.forEach(function(run, index) {          
        var row         = leaderboardBody.insertRow();
        var rankCell    = row.insertCell();
        var playerCell  = row.insertCell();
        var timeCell    = row.insertCell();
        var dateCell    = row.insertCell();
        var pointsCell  = row.insertCell();

        rankCell.textContent = run.place;

        if (run.player !== "Anonymous") {
            if (run.countrycode) {
                const countryFlag = run.countrycode === "vh" ? '<img src="https://www.speedrun.com/images/flags/vh.png" height="15" />' : `<img src="https://flagcdn.com/h20/${run.countrycode}.png" height="15" />`;
                playerCellContent = `${countryFlag} <a href="/player/${run.player}">${run.nickname || run.player}</a>`;
            } else {
                playerCellContent = `<a href="/player/${run.player}">${run.nickname || run.player}</a>`;
            }
            
            if (run.player2) {
                playerCellContent += " &";
                if (run.countrycode2) {
                const countryFlag = run.countrycode2 === "vh" ? '<img src="https://www.speedrun.com/images/flags/vh.png" height="15" />' : `<img src="https://flagcdn.com/h20/${run.countrycode2}.png" height="15" />`;
                playerCellContent += ` ${countryFlag} <a href="/player/${run.player2}">${run.player2nickname || run.player2}</a>`;
                } else {
                playerCellContent += ` ${run.player2nickname || run.player2}`;
                }
            }
            } else {
                playerCellContent = "Anonymous";
            }

        playerCell.innerHTML = playerCellContent;          
        timeCell.innerHTML = '<a href="' + run.url + '" target="_blank">' + run.time + '</a>';
        pointsCell.textContent = run.points;

        var formattedDate = new Date(run.date).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            timeZone: "UTC"
        });
        dateCell.textContent = formattedDate;
    });
}

document.addEventListener("DOMContentLoaded", function() {
    var subcategoryDropdown = document.getElementById("subcategory-dropdown");

    subcategoryDropdown.addEventListener("change", function() {
        var selectedSubcategory = subcategoryDropdown.value;
        updateLeaderboard(selectedSubcategory);
    });

    updateLeaderboard(subcategoryDropdown.value);
});