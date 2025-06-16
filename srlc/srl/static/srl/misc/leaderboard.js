$(document).ready(function () {
    var originalLeaderboard = JSON.parse(document.getElementById("leaderboard-data").textContent);

    function populateLeaderboard(data) {
        var tableBody = document.getElementById("leaderboardTable").getElementsByTagName('tbody')[0];
        tableBody.innerHTML = '';

        const getPlayerLink = (player, nickname) => {
            const linkText = nickname || player;
            return '<a href="/player/' + player + '">' + linkText + '</a>';
        };

        const getCountryFlag = (countrycode) => {
            if (!countrycode) {
                return "";
            }

            const countryFlag = countrycode === "vh" ?
                `<img src="../srl/misc/vh.png" alt="${run.countryname}" title="${run.countryname}" height="15" />` :
                `<img src="https://flagcdn.com/h20/${countrycode}.png" alt="${run.countryname}" title="${run.countryname}" height="15" />`;

            return countryFlag;
        };

        data.forEach(function (item, index) {
            var row = tableBody.insertRow();
            var rankCell = row.insertCell();
            var playerCell = row.insertCell();
            var pointsCell = row.insertCell();

            const playerCellContent = getCountryFlag(item.countrycode) + '' + getPlayerLink(item.player, item.nickname);

            rankCell.textContent = item.rank;
            playerCell.innerHTML = playerCellContent;
            pointsCell.textContent = item.total_points;
        });
    }

    $("#searchForm").submit(function (event) {
        event.preventDefault();
        var searchQuery = $("#searchInput").val().trim();
        if (searchQuery === "") {
            populateLeaderboard(originalLeaderboard);
            return;
        }
        var url = "{% url 'search_leaderboard' %}";
        $.ajax({
            url: url,
            data: { search: searchQuery },
            success: function (data) {
                populateLeaderboard(data);
            }
        });
    });
});