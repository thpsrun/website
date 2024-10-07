function updateMonthlyLeaderboard(selectedMonth) {
    var playerTotalsJSON        = JSON.parse(document.getElementById("player-totals").textContent);
    var leaderboardTable        = document.getElementById("leaderboard-table");
    var leaderboardBody         = leaderboardTable.getElementsByTagName("tbody")[0];

    leaderboardBody.innerHTML   = "";

    function getSelectedMonthData(playerTotalsJSON, selectedMonth) {
        for (var key in playerTotalsJSON) {
            if (key === selectedMonth) {
                return playerTotalsJSON[key];
            }
        }
        return [];
    }

    var selectedMonthData = getSelectedMonthData(playerTotalsJSON, selectedMonth);

    for (var i = 0; i < selectedMonthData.length; i ++){
        var row         = leaderboardBody.insertRow();
        var rankCell    = row.insertCell();
        var playerCell  = row.insertCell();
        var pointsCell  = row.insertCell();
        var runsCell    = row.insertCell();

        var item = selectedMonthData[i];

        rankCell.textContent = item[1].rank;
        if (item[1].countrycode){
            if (item[1].nickname){
                playerCellContent = '<img src="https://flagcdn.com/h20/' + item[1].countrycode + '.png" height="15" />' + ' ' + '<a href="/player/' + item[0] + '">' + item[1].nickname + '</a>';
            }
            else{
                playerCellContent = '<img src="https://flagcdn.com/h20/' + item[1].countrycode + '.png" height="15" />' + ' ' + '<a href="/player/' + item[0] + '">' + item[0] + '</a>';
            }
        } else{
            if (item[1].nickname){
                playerCellContent = '<a href="/player/' + item[0] + '">' + item[1].nickname + '</a>'
            }
            else{
                playerCellContent = '<a href="/player/' + item[0] + '">' + item[0] + '</a>'
            }
        }
        playerCell.innerHTML    = playerCellContent;
        pointsCell.textContent  = item[1].points;
        runsCell.textContent    = item[1].runs;
    }    
}

document.addEventListener("DOMContentLoaded", function() {
    var subcategoryDropdown = document.getElementById("month-menu");

    subcategoryDropdown.addEventListener("change", function() {
        var selectedMonth = subcategoryDropdown.value;
        updateMonthlyLeaderboard(selectedMonth);
    });

    updateMonthlyLeaderboard(subcategoryDropdown.value);
});