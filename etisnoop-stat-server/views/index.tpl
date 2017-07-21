<!DOCTYPE html>
<html><head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <title>ETISnoop Stats</title>
	<link rel="stylesheet" href="static/style.css" type="text/css" media="screen" charset="utf-8"/>
</head>
<body>
    <h1>Some ETISnoop statistics</h1>

    <ul id="info-nav">
        <li><a href="#general">General</a></li>
    </ul>

    <div id="info">
        <div id="general">
            <p>General Options</p>
            <ul>
                <li>frequency: {{freq}}</li>
                <li>gain: {{gain}}</li>
            </ul>
        </div>

        <div id="stats">
            <p>This shows some ETISnoop stats</p>
            <pre>{{stats}}</pre>
        </div>
    </div>
</body>
</html>

