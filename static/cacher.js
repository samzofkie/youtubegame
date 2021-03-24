var ytp1, ytp2;
var id_index = 0, counter = 0;
var intervalId = null;
var totalsecs = 0; 
var interactions = {};
var VIDS_LEFT_REUP_THRESHOLD = 5;
var reporting = false;

function createYTPlayer(div_id, vid_id) {
    return new YT.Player(div_id,
                         { height: '600', width: '925',
                           videoId: vid_id,
                           events: { 'onReady': onPlayerReady,
                                     'onStateChange': onPlayerStateChange
                                   }
                         }
                        );
}

function onYouTubeIframeAPIReady() {
    for (var i=1; i<=2; i++) {
        window['ytp'+String(i)] = createYTPlayer('player'+String(i), ids[id_index++]);
    }
}


function onPlayerReady(event) {
    if (event.target.getIframe().id === 'player2') {
		event.target.getIframe().style.display = 'none';
	}
}

function onPlayerStateChange(event) {
    if (event.data === 1) start();
    if (event.data === 2) stop();
}

function start() {
    intervalId = setInterval( () => {++totalsecs;}, 1000 );
}

function stop() {
    if (intervalId)
        clearInterval(intervalId);
}


window.onload = () => {
    document.getElementById('btn').onclick = next_video;
	document.addEventListener('keydown', reveal_reporting);
}

function reveal_reporting(e) {
	console.log(e.code);
	var cb = document.getElementById('reporting_checkbox');
	if (e.key === 'u') {
		if (cb.style.display === 'none') {
			cb.style.display = '';
		} else {
			cb.style.display = 'none';
		}
	}
}

function reporting_true() {
	reporting = true;
}

function next_video(e) {
    
    // hide cur if
    var ole_ytp = window['ytp'+String(counter++ %2+1)];
    ole_ytp.getIframe().style.display = 'none';
    
    // cue nu vid
    ole_ytp.cueVideoById(ids[id_index++]);

    // reveal new if
    window['ytp'+String(counter%2+1)].getIframe().style.display = '';
     
    // if tryna write vid watch time to json
    interactions[ids[id_index-3]] = totalsecs;
    totalsecs = 0;
    
    // if low on vids reup
    if (id_index + VIDS_LEFT_REUP_THRESHOLD > ids.length) {
       reup(); 
    }

    // every five vids report bakc to serva
    if (reporting && id_index%5===0) {
        report();
    }
}


function reup() {
    var xhr = new XMLHttpRequest();
	xhr.open("GET", "/more", true);
	xhr.onload = function(e) {
		if (xhr.status === 200) {
			ids = ids.concat( JSON.parse(xhr.responseText) );
   		} else if (xhr.status === 429) { punish();}	
	};
	xhr.onerror = function(e) {
		console.error('reup err: ', xhr.statusText);
	};
	xhr.send();
}

function report() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST','/report', true);
    xhr.send(JSON.stringify(interactions));
    interactions = {};
}


function punish() {
    // Let em know they were going too fast
    var button = document.getElementById('btn');
	var warning = document.createElement("div");
	warning.style.color = 'white';
	warning.innerTEXT = "U gotta slow down chill for 1 min";
	document.body.appendChild(warning);
	
	// Take away the precious button for 60 secs
	button.onclick = ()=>{ console.log("click") };
    button.style.opacity = 0.6;
	setTimeout( ()=>{ 
		// Take away warning and restore button
		button.onclick = next_video;
        button.style.opacity = 1;
		warning.remove()
	}, 60000 );
}

