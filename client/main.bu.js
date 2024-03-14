window.onload = function() {
    console.log("Starting fetch request...");
    document.getElementById('wiki-form').addEventListener('submit', function(event) {
    event.preventDefault();

    var startPage = document.getElementById('start-page').value;
    var finishPage = document.getElementById('finish-page').value;

    var logsElement = document.getElementById('logs');
    console.log("Sending fetch request...");
    fetch('/find_path', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start: startPage,
            finish: finishPage
        })
    })
    .then(response => {
        if (response.status === 429) {
            throw new Error('You have made too many requests. Please try again later.');
        }
        return response.json();
    })
    .catch(error => {
        console.error('Error:', error);
        logsElement.innerHTML = error.message + (data && data.time ? '<p>Elapsed time: ' + data.time + '</p>' : '');
    })
    .then(data => {
        if (!data) return; // if there was an error, data will be undefined
        console.log(data);
        // output path
        var pathElement = document.getElementById('path');
        var pathHtml = '<ul>';
        pathElement.innerHTML = ''; // clear previous path
        logsElement.innerHTML = ''; // clear previous logs
        var statsElement = document.getElementById('stats');
        data.path.forEach(function(page) {
            pathHtml += '<li><a href="' + page + '">' + decodeURIComponent(page) + '</a></li>';
        });
        pathHtml += '</ul>';
        pathElement.innerHTML = pathHtml;
        // output discovered pages 
        var logsElement = document.getElementById('logs');
        var logsHtml = '<pre>';
        data.logs.forEach(function(log) {
            logsHtml += log + '\n';
        });
        logsHtml += '</pre>';
        logsElement.innerHTML = logsHtml;
        // output stats
        var statsElement = document.getElementById('stats');
        var statsHtml = '<ul>';
        statsHtml += '<li>Elapsed time: ' + data.time + '</li>';
        statsHtml += '<li>Number of discovered pages: ' + data.logs.length + '</li>';
        statsHtml += '</ul>';
        console.log(statsHtml);
        console.log(statsElement);
        statsElement.innerHTML = statsHtml;
    });
    console.log("Finished fetch request...");
    });
};
