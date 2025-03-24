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

        let playerCellContent = '';
        if (run.player !== "Anonymous") {
            const getPlayerLink = (player, nickname) => {
                const linkText = nickname || player;
                return '<a href="/player/' + player + '">' + linkText + '</a>';
            };
        
            const getCountryFlag = (countrycode) => {
                if (!countrycode) {
                    return "";
                }
              
                const countryFlag = countrycode === "vh" ? 
                    `<img src="https://www.speedrun.com/images/flags/vh.png" alt="${run.countryname}" title="${run.countryname}" height="15" />` : 
                    `<img src="https://flagcdn.com/h20/${countrycode}.png" alt="${run.countryname}" title="${run.countryname}" height="15" />`;
              
                return countryFlag;
              };
            
            const player1Link = getPlayerLink(run.player, run.nickname);
            const player1Content = getCountryFlag(run.countrycode) + ' ' + player1Link;

            playerCellContent = player1Content;

            if (run.player2) {
                if (run.player2 !== "Anonymous") {
                    const player2Link = getPlayerLink(run.player2, run.player2nickname);
                    const player2Content = ' & ' + getCountryFlag(run.countrycode2) + ' ' + player2Link;
                    playerCellContent += ' ' + player2Content;
                } else {
                    playerCellContent += ' & ' + "Anonymous";
                }
            }
        } else {
            playerCellContent = "Anonymous";
        }

        playerCell.innerHTML = playerCellContent;
        timeCell.innerHTML = '<a href="' + run.url + '" target="_blank">' + run.time + '</a>';
        pointsCell.textContent = run.points;

        if (run.date) {
            var formattedDate = new Date(run.date).toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
                timeZone: "UTC"
            });
            dateCell.textContent = formattedDate;
        } else {
            dateCell.innerHTML = ' --- ';
        }
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