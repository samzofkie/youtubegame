var i=0, j=0, k=0;
var iframes = new Array();

// put first videos from html into iframes array
for (; k<ids.length; k++) {
	iframes.push(createIframe( ids[k], k ));
}

window.onload = function() {
	
	// actually create 3 iframes
	for (; j<3; j++) {
		document.body.insertBefore( iframes[j], document.getElementById('myBtn'));
	}
	 
	// reveal first iframe
	var elem = document.getElementById('iframe_id'+i);
	elem.style.display = 'block';
	i++;	
	
	document.getElementById('myBtn').onclick = next_video;
}	


function next_video(e) {
	// del iframe_id i-1
	elem = document.getElementById('iframe_id'+(i-1));
	elem.parentNode.removeChild(elem);
				
	// reveal iframe_id i
	var elem = document.getElementById('iframe_id'+i);
	elem.style.display = 'block';

	// load an iframe in the background
	document.body.insertBefore( iframes[j], document.getElementById('myBtn'));


	j++;
	i++;	

	// if we're almost out of iframes, get more
	if (iframes.length-5 < j) {
		var xhr = new XMLHttpRequest();
		xhr.open("GET", xhr_endpoint, true);
		xhr.onload = function(e) {
			if (xhr.status === 200) {
				// process new ids and add them to iframes array
				var ids = JSON.parse(xhr.responseText);
				var start = k;
				for (; k < start + ids.length; k++) {
					iframes.push(createIframe(ids[k-start], k));
				}
			}
		}
		xhr.onerror = function(e) {
			console.error(xhr.statusText);
		};
		xhr.send(null);
	}				
}


function createIframe(vid_id,i) {
	var iframe = document.createElement('iframe');
	iframe.id = 'iframe_id'+i;
	iframe.height = 600;
	iframe.width = 1000;
	iframe.frameBorder = 0;
	iframe.src = 'https://www.youtube.com/embed/'+vid_id;
	iframe.style.display = 'none';
	return iframe;
}


