// There are three counters: created_counter counts the number of iframes created by createIframe, and held in the iframes array
// 			     inserted_counter counts the number of iframes inserted into the html (first loop of window.onload)
// 			     revealed_counter counts the number of iframes revealed (iframe.style.display = 'block' as opposed to 'none'
// These are all global variables so they can be shared between window.onload and next_video.

var iframes = new Array();

var created_counter = 0, inserted_counter = 0, revealed_counter = 0;

var button;

// Create first iframes with ids from ids variable (in html), and put them in iframes array.
for (created_counter=0; created_counter < ids.length; created_counter++) {
	iframes.push(createIframe( ids[created_counter], created_counter ));
}

window.onload = function() {

	button = document.getElementById('myBtn');

	// Insert 3 iframes from iframes array into document before button
	for (inserted_counter = 0; inserted_counter < 3; inserted_counter++) {
		document.body.insertBefore( iframes[inserted_counter], button);
	}
	 
	// Reveal first iframe
	var tmp_if = document.getElementById('iframe_id' + revealed_counter);
	tmp_if.style.display = 'block';
	revealed_counter++;	
	
	// Register next_video function with button
	button.onclick = next_video;
}	


function next_video(e) {
	// Remove iframe w iframe_id revealed_counter-1
	tmp_if = document.getElementById('iframe_id' + (revealed_counter-1));
	tmp_if.parentNode.removeChild(tmp_if);
				
	// Reveal iframe w iframe_id revealed_counter
	var tmp_if = document.getElementById('iframe_id' + revealed_counter);
	tmp_if.style.display = 'block';

	// Insert an iframe from iframes array
	document.body.insertBefore( iframes[inserted_counter], button);

	inserted_counter++;
	revealed_counter++;	

	// If there's less than 5 iframes in iframes array, make xhr request for more
	if (iframes.length - 5 < inserted_counter) {
		var xhr = new XMLHttpRequest();
		xhr.open("GET", xhr_endpoint, true);
		xhr.onload = function(e) {
			if (xhr.status === 200) {
				// Create new iframes from ids array, and add them to iframes array
				var ids = JSON.parse(xhr.responseText);
				var start = created_counter;
				for (; created_counter < start + ids.length; created_counter++) {
					iframes.push(createIframe( ids[created_counter - start], created_counter ));
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


