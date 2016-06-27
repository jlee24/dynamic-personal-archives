function _get(url, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onload = function() {
		cb(this.responseText);
    }
    xhr.send();
}

function _get_json(url, cb) {
    _get(url, function(dat) {
		cb(JSON.parse(dat));
	});
}

var db = [];
var aoa;
var window_padding = 20;

var Timeline = function(data) {
    this.$el = document.createElement("div");
    this.$el.className = "archive";

    this.$taglist = document.createElement("div");
    this.$taglist.className = "taglist";
    this.$el.appendChild(this.$taglist);

    this.$strips = document.createElement("div");
    this.$strips.className = "strips";
    this.$el.appendChild(this.$strips);

    this.$bars = document.createElement("div");
    this.$bars.className = "barcont";
    this.$el.appendChild(this.$bars);

    this.$strip_info = document.createElement("div");
    this.$strip_info.className = "strip_info";
    this.$el.appendChild(this.$strip_info);

    this.hires_ims$ = {};	// uid -> $im
    this._ims_loading = {};	// uid -> cb

    this.data = data;

    this.tags = {};		// Tagname -> [idx, ]

    this.cur_hover = null;
    this.cur_detail = null;
    this.cur_tag = null;    
    this.cur_tag_preview = null;    

    this.imgs$ = [];
    this.bars$ = [];
    this.infos$ = [];
    
    this.load_images();
    this.load_tags();
    this.load_timeline();
    this.load_info();

    this.render_tags();
    this.render();

    window.onresize = function() {
	this.render();
    }.bind(this);
}

Timeline.prototype.load_hires = function(uid, cb) {
    if(uid in this.hires_ims$) {
		// already loaded
		cb(this.hires_ims$[uid]);
		return;
    }
    if(uid in this._ims_loading) {
		// already loading - clobber cb
		this._ims_loading[uid] = cb;
		return;
    }

    // load
    var $im = document.createElement("img");
    $im.src = "/static/jpg/archive-" + uid + "-320x.jpg";
    this._ims_loading[uid] = cb;
    $im.onload = function() {
		this.aoa.hires_ims$[uid] = this.$im;
		// hit CB if it exists
		if(this.aoa._ims_loading[uid]) {
		    this.aoa._ims_loading[uid](this.$im);
		}
    }.bind({aoa: this, "$im": $im});
}

Timeline.prototype.render_tags = function() {
    var tagnames = Object.keys(this.tags);
    var c_title = document.getElementById("cat_title");
    var c_title_store = c_title.innerHTML;

    tagnames.sort();
    tagnames
	.forEach(function(tag) {
	    var $tag = document.createElement("div");
	    $tag.className = "tag " + tag;
	    $tag.title = tag;
	    $tag.onmouseover = function() {
			this.preview_tag(tag);
			c_title.innerHTML = 'Categories: Hover: '+tag;
	    }.bind(this);
	    $tag.onmouseout = function() {
			// show all
			this.preview_tag("");
			c_title.innerHTML = c_title_store;
	    }.bind(this);
	    $tag.onclick = function() {
			/*revert other cat_buttons*/
			var d = document.getElementsByClassName("tag"),
	      		len = d !== null ? d.length : 0,
			    i = 0;
			for(i; i < len; i++) {
			    d[i].className = d[i].className.replace('cat_selected','');
			}

			if(this.cur_tag != tag) {
			    this.show_tag(tag);
		    	$tag.className = "tag " + tag + " cat_selected";
		    	//$tag.className = tag + " cat_selected";
			}
			else {
			    this.show_tag("");
			    $tag.className = "tag " + tag;
			    //$tag.className = tag;
			}
	    }.bind(this);
	    this.$taglist.appendChild($tag);
	}, this);
}
Timeline.prototype.preview_tag = function(tag) {
    this.cur_tag_preview = tag;
    this.render();
}
Timeline.prototype.show_tag = function(tag) {
    // Hide detail
    this.cur_detail = null;
    
    this.cur_tag = tag;
    this.render();
}
Timeline.prototype.show_detail = function(idx) {
    this.cur_detail = idx;
    this.render();

    // Swap in hires image
    if(idx !== null) {
		this.load_hires(this.data[idx]._id, function($im) {
		    var $par = this.imgs$[idx];
		    // swap
		    console.log("par", $par);
		    $par.removeChild($par.querySelector("img"));
		    $par.appendChild($im);
		    
		}.bind(this));
    }
}

Timeline.prototype.show_hover = function(idx) {
     this.cur_hover = idx;
     this.render();
}

Timeline.prototype.load_tags = function() {
    this.data
	.forEach(function(x, idx) {
		if (!(x.TYPE in this.tags)) {
			this.tags[x.TYPE] = [];
		}
		this.tags[x.TYPE].push(idx);
	}, this);
}

Timeline.prototype.load_timeline = function() {
    var cur_year;
    
    this.data
	.forEach(function(x, idx) {
	    var $div = document.createElement("div");
	    $div.className = "bars";
	    this.bars$.push($div);

	    var year = get_start_year(x);
	    if(year != cur_year) {
			cur_year = year;

			if(year > 2009) {
			    var $year = document.createElement('span');
			    $year.className = "year";
			    $year.textContent = "" + year;
			    $div.appendChild($year);
			}
		}
	    
	    this.$bars.appendChild($div);
	    
	    get_type(x)
		.forEach(function(tagname, cat_idx) {
		    var $tbar = document.createElement("div");
		    $tbar.className = tagname;
		    $tbar.title = tagname;
		    $tbar.style.top = 3*cat_idx;
		    $div.appendChild($tbar)
		});
	}, this);
}

Timeline.prototype.load_info = function() {
    this.data
	.forEach(function(x, idx) {
	    var $div = document.createElement("div");
	    $div.className = "infos";
	    this.infos$.push($div);
	    this.$strip_info.appendChild($div);

		var $ainfo = document.createElement("div");
		$ainfo.className = get_titles(x);
		$ainfo.title = get_titles(x);
		$ainfo.innerHTML = '<a href="'+get_url(x)+'" target="_blank">[open]</a> '+get_titles(x).replace(/_/g, ' ');;
		// $ainfo.style.top = 3*arch_idx;
		$div.appendChild($ainfo);
	}, this);
}

Timeline.prototype.load_images = function() {
    this.data
	.forEach(function(x, idx) {
	    var $imcont = document.createElement("div");
	    $imcont.className = "imcont";
	    
	    var $img = document.createElement("img");
	    // Start with low resolution image
	    $img.src = "/static/jpg/archive-" + x._id + "-60x.jpg";
	    $imcont.onclick = function() {
			if(this.cur_detail == idx) {
			    this.show_detail(null);
			}
			else {
			    this.show_detail(idx);
			}
	    }.bind(this);
	    /*ON HOVER STRIP, SHOW TITLE*/
	    $imcont.onmouseover = function() {
	    	this.show_hover(idx);
	    }.bind(this);

	    $imcont.appendChild($img);
	    
	    this.$strips.appendChild($imcont);
	    this.imgs$.push($imcont);
	}, this)
}
Timeline.prototype.render = function() {
    var page_w = document.body.clientWidth - 2*window_padding;
	
    //set selected category (tag) label
    var c_title = document.getElementById("cat_title");

    var nimages = this.data.length;

    if(this.cur_tag) {
		nimages = this.data
		    .filter(function(x) {
		    	console.log(x.TYPE);
		    	console.log(this.cur_tag);
		    	return x.TYPE == this.cur_tag;
				//return x.TYPE.indexOf(this.cur_tag) >= 0;
		    }, this).length;
		c_title.innerHTML = 'Categories: Selected: '+ this.cur_tag;
    }
    else {
		c_title.innerHTML = 'Categories: Select a category';
    }
	
    // Basic render
    var cur_x = 0;

    var img_w = Math.min(60, Math.max(5, Math.floor(page_w / nimages) - 3));
    var padding = (page_w - (img_w*nimages)) / nimages;

    if(this.cur_detail) {
		padding = (page_w - (img_w*(nimages-1)) - 320) / nimages;
    }

    padding = Math.min(20, padding);
    
    this.imgs$
	.forEach(function($img, idx) {
	    var row = this.data[idx];
	    
	    var $info = this.infos$[idx];
	    var $bars = this.bars$[idx];

	    var $divs = [$img, $info, $bars];

	    if (this.cur_tag && this.cur_tag != row.TYPE) {
	    //if(this.cur_tag && row.TYPE.indexOf(this.cur_tag) < 0) {
			// Not in category: don't display
			$divs.forEach(function(x) { x.style.left = page_w + 2*window_padding; });
			return;
	    }

	    $divs.forEach(function(x) { x.style.left = cur_x+window_padding; });

	    if (this.cur_tag_preview && this.cur_tag_preview != row.TYPE) {
	    //if(this.cur_tag_preview && row.TYPE.indexOf(this.cur_tag_preview) < 0) {
		// Not in hover category
			$divs.forEach(function(x) { x.classList.remove("preview"); })
	    }
	    else {
		// Shown in full
			$divs.forEach(function(x) { x.classList.add("preview"); })
	    }
	    
	    if(this.cur_detail === idx) {
			cur_x += 320 + padding;
			$divs.forEach(function(x) {
			    x.style.width = 320;
			    x.classList.add("detail");
			});
	    }
	    else {
			$divs.forEach(function(x) {
			    x.style.width = img_w;
			    x.classList.remove("detail");
			})
			
			cur_x += img_w + padding;
		}

		if(this.cur_hover === idx) {
			$info.classList.add("infovisible");
			$info.style.width = 320;
		}
		else {
			$info.classList.remove("infovisible");
			$info.style.width = img_w;
		}
	}, this);
}

_get_json("/static/db.json", function(ret) {

    db = ret;
    db.forEach(function(x,idx) {
	x._id = idx;
    });

    // Sort by start
    db.sort(function(x,y) {
		return get_start_year(x) > get_start_year(y) ? 1 : -1;
    });

    aoa = new Timeline(db);
    document.body.appendChild(aoa.$el);

})

function get_start_year(x) {
	return x.YEAR;
}
function get_type(x) {
	var arr = [];
	arr.push(x.TYPE);
	return arr;
}

function get_titles(x) {
    return x.TITLE;
}    

function get_url(x) {
    return x.SOURCE;
}