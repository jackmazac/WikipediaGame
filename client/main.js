console.log("Starting fetch request...");
document.getElementById('wiki-form').addEventListener('submit', function(event) {
    event.preventDefault();

    var startPage = document.getElementById('start-page').value;
    var finishPage = document.getElementById('finish-page').value;

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
        var pathElement = document.getElementById('path');
        pathElement.innerHTML = '<p>Error: ' + error.message + '</p>';
        return error.response.json();
    })
    .then(data => {
        if (!data) return; // if there was an error, data will be undefined
        var logsElement = document.getElementById('logs');
        logsElement.innerHTML = data.error + (data.time ? '<p>Elapsed time: ' + data.time + '</p>' : '');
        return data; // return data so it can be used in the next .then block
    })
    .then(data => {
        if (!data) return; // if there was an error, data will be undefined
        console.log('about to output data')
        console.log(data);
        // output path
        console.log('about to output path')
        var pathElement = document.getElementById('path');
        pathElement.innerHTML = ''; // clear previous path
        var pathHtml = '<ul>';
        data.path.forEach(function(page) {
            pathHtml += '<li><a href="' + page + '">' + decodeURIComponent(page) + '</a></li>';
        });
        pathHtml += '</ul>';
        pathElement.innerHTML = pathHtml;
        // output discovered pages 
        console.log('about to output logs')
        var logsElement = document.getElementById('logs');
        logsElement.innerHTML = ''; // clear previous logs
        var logsHtml = '<pre>';
        data.logs.forEach(function(log) {
            logsHtml += log + '\n';
        });
        logsHtml += '</pre>';
        logsElement.innerHTML = logsHtml;
        // output stats
        console.log('about to output stats')
        var statsElement = document.getElementById('stats');
        statsElement.innerHTML = ''; // clear previous stats
        var statsHtml = '<ul>';
        statsHtml += '<li>Elapsed time: ' + data.time + '</li>';
        statsHtml += '<li>Number of discovered pages: ' + data.discovered + '</li>';
        statsHtml += '</ul>';
        statsElement.innerHTML = statsHtml;
    });
});
console.log("Finished fetch request...");
