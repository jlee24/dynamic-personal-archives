var search = function() {
	var query = document.getElementById("query").value;
	var xhr = new XMLHttpRequest();
	xhr.open("GET", "/?query=" + query, true);
	xhr.onload = function(e) {
			var search_results = xhr.getResponseHeader('search_results');
			// console.log(search_results);
			search_results = JSON.parse(search_results);
			show_search_results(search_results);
	}
	xhr.send();
}

var show_search_results = function(search_results) {
	d3.select('svg').select('#g_slices').selectAll('rect').filter(function() {return this.getAttribute('class') == 'rect_res selected'})
		.transition()
		.duration(0)
		.attr('class', 'rect_res not_selected')
		.style('fill-opacity', 0.5)

	for (var i = 0; i < 5; i++) {
		d3.select('svg').select("rect[id='" + parseInt(search_results[i.toString()]['doc_id']) + "']")
			.transition()
			.duration(0)
			.attr('class', 'rect_res selected')
			.style('fill-opacity', function() {
				return search_results[i.toString()]['sim_score'];
			})
	}
}

var unstem = {
	'comput': 'computer',
	'peopl': 'people',
	'devic': 'device',
	'mous': 'mouse',
	'termin': 'terminate'
}

var round_down = function(num, divisor) {
	if (num % divisor != 0) return num - (num % divisor);
	else return num;
}

var round_up = function(num, divisor) {
	if (num % divisor != 0) return num + (divisor - (num % divisor));
	else return num;
}

var arraysEqual = function(a, b) {
	if (a === b) return true;
	if (a == null || b == null) return false;
	if (a.length != b.length) return false;
}

function visavailChart(corpus, influences) {
	// define chart layout
	var margin = {
		// top margin includes title and legend
		top: 70,

		// right margin should provide space for last horz. axis title
		right: 40,

		bottom: 20,

		// left margin should provide space for y axis titles
		left: 100,
	};

	var corpus = corpus;
	var influences = influences;
	console.log(influences);
	var themes = influences.themes;
	var num_slices = influences.info.num_slices;
	var num_topics = influences.info.num_topics;

	// height of horizontal data bars
	var dataHeight = 18;

	// spacing between horizontal data bars
	var lineSpacing = 14;

	// vertical space for heading
	var paddingTopHeading = -50;

	// vertical overhang of vertical grid lines on bottom
	var paddingBottom = 10;

	// space for y axis titles
	var paddingLeft = -100;

	var width = 980 - margin.left - margin.right;
	// var width = screen.width * 0.60;

	// title of chart is drawn or not (default: yes)
	var drawTitle = 1;

	// year ticks to be emphasized or not (default: yes)
	var emphasizeYearTicks = 1;

	// define chart pagination
	// max. no. of datasets that is displayed, 0: all (default: all)
	var maxDisplayDatasets = 0;

	// dataset that is displayed first in the current
	// display, chart will show datasets "curDisplayFirstDataset" to
	// "curDisplayFirstDataset+maxDisplayDatasets"
	var curDisplayFirstDataset = 0;

	// global div for tooltip
	var div = d3.select('body').append('div')
			.attr('class', 'tooltip_')
			.style('opacity', 0);

	function chart(selection) {
		selection.each(function drawGraph(dataset) {
			// check which subset of datasets have to be displayed
			var maxPages = 0;
			var startSet;
			var endSet;
			if (maxDisplayDatasets !== 0) {
				startSet = curDisplayFirstDataset;
				if (curDisplayFirstDataset + maxDisplayDatasets > dataset.length) {
					endSet = dataset.length;
				} else {
					endSet = curDisplayFirstDataset + maxDisplayDatasets;
				}
				maxPages = Math.ceil(dataset.length / maxDisplayDatasets);
			} else {
				startSet = 0;
				endSet = dataset.length;
			}

			// append data attribute in HTML for pagination interface
			selection.attr('data-max-pages', maxPages);

			var noOfDatasets = endSet - startSet;
			// var height = dataHeight * noOfDatasets + lineSpacing * noOfDatasets - 1;
			// var height = 0;

			// check how data is arranged
			var definedBlocks = 0;

			console.log(themes);
			var _themes = [];
			for (var i = 0; i < themes.length; i++) {
				_topic = {}
				_topic['measure'] = "Theme " + i.toString();
				_topic['data'] = ["1960", 9, "2005", themes[i]];
				_themes.push(_topic);
			}
			console.log(_themes);

			// parse data text strings to JavaScript date stamps
			var parseDate = d3.time.format('%Y');

			dataset.forEach(function (d) {
				d.data.forEach(function (d1) {
					if (!(d1[0] instanceof Date)) {
						d1[0] = parseDate.parse(d1[0]);
						d1[2] = parseDate.parse(d1[2]);
					}
				});
			});

			_themes.forEach(function (d) {
				if (!(d.data[0] instanceof Date)) {
						d.data[0] = parseDate.parse(d.data[0]);
						d.data[2] = parseDate.parse(d.data[2]);
				}
			});

			// cluster data by dates to form time blocks
			dataset.forEach(function (series, seriesI) {
				var tmpData = [];
				var dataLength = series.data.length;
				series.data.forEach(function (d, i) {
					tmpData.push(d);
				});
				dataset[seriesI].disp_data = tmpData;
			});

			_themes.forEach(function (series, seriesI) {
				var tmpData = [];
				var dataLength = series.data.length;
				tmpData.push(series.data);
				_themes[seriesI].disp_data = tmpData;
			});

			// determine start and end dates among all nested datasets
			var startDate = 0;
			var endDate = 0;
			var parseYear = d3.time.format('%Y');

			dataset.forEach(function (series, seriesI) {
				if (seriesI === 0) {
					// startDate = series.disp_data[0][0];
					var startYear = round_down(series.disp_data[0][0].getFullYear(), 10);
					startDate = parseYear.parse(startYear.toString());
					var endYear = round_up(series.disp_data[series.disp_data.length - 1][2].getFullYear(), 5);
					endDate = parseYear.parse(endYear.toString());
				} else {
					if (series.disp_data[0][0] < startDate) {
						var startYear = round_down(series.disp_data[0][0].getFullYear(), 10);
						startDate = parseYear.parse(startYear.toString());
					}
					if (series.disp_data[series.disp_data.length - 1][2] > endDate) {
						var endYear = round_up(series.disp_data[series.disp_data.length - 1][2].getFullYear(), 10);
						endDate = parseYear.parse(endYear.toString());
					}
				}
			});

			// define scales
			var xScale = d3.time.scale()
					.domain([startDate, endDate])
					.range([0, width])
					.clamp(1);

			// define axes
			var xAxis = d3.svg.axis()
					.scale(xScale)
					.ticks(d3.time.years, 10)//should display 1 year intervals
					.tickFormat(d3.time.format('%Y'))//%Y-for year boundaries, such as 2011
					.orient('top');

			// create SVG element
			var svg = d3.select(this).append('svg')
					.attr('width', width + margin.left + margin.right)
					// .attr('height', height + margin.top + margin.bottom)
					.append('g')
					.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

			// create basic element groups
			svg.append('g').attr('id', 'g_title');
			svg.append('g').attr('id', 'g_axis');
			svg.append('g').attr('id', 'g_data');
			svg.append('g').attr('id', 'g_topics');
			svg.append('g').attr('id', 'g_slices');
			svg.append('g').attr('id', 'g_icons');
			
			function highlight_res_in_period(start, end, turn_on) { // start and end years
				svg.select('#g_slices').selectAll('rect').filter(function() {return this.getAttribute('class') !== 'border'})
					.transition()
					.duration(0)
					.each(function (d) {
						var res_year = parseYear.parse(d.YEAR);
						if (res_year >= start && res_year <= end) {
							var rect = document.getElementById(this.id);
							if (turn_on) rect.style.fillOpacity = Number(rect.style.fillOpacity) + 0.25;
							else rect.style.fillOpacity = Number(rect.style.fillOpacity) - 0.25;
						}
					})
				}

			var show_influenced_documents = function(topic, slice, i_topic, turn_on) {
				var topic_index = i_topic;
				var influencing_docs = [];

				for (var i = slice; i < num_slices-1; i++) {
					// find index of topic
					var topics = influences['time_slice_' + i.toString() + '_topics'];
					for (var j = 0; j < num_topics; j++) {
						if (topics[j] === topic) {
							topic_index = j;
						}
					}

					var docs = influences['time_slice_' + i.toString()];
					var max_influence = 0.0;
					var max_influencing_doc;

					var sortable = [];
					for (var doc in docs) {
						sortable.push(doc);
					}
					sortable.sort(function(a, b) {
						return docs[b][topic_index] - docs[a][topic_index];
					})
					sortable = sortable.slice(0,4);
					influencing_docs.push.apply(influencing_docs, sortable);
				}

				for (var i = 0; i < influencing_docs.length; i++) {
					d3.select('svg').select("rect[id='" + parseInt(influencing_docs[i].match(/\d+/)) + "']")
						.transition()
						.duration(0)
						.attr('class', function() {
							var rect = document.getElementById(this.id);
							if (turn_on) {
								// if (this.getAttribute('class') === 'rect_res not_selected') return 'rect_res selected';
								// else return this.getAttribute('class') + '_selected';
								if (this.getAttribute('class') === 'rect_res not_selected') {
									rect.style.fillOpacity = 1.25;
									return 'rect_res selected';
								} else {
									rect.style.fillOpacity = Number(rect.style.fillOpacity) + 0.25;
									return 'rect_res selected';
								}
							} else {
								if (rect.style.fillOpacity === 1) return 'rect_res not_selected';
								else {
									rect.style.fillOpacity = Number(rect.style.fillOpacity) - 0.25;
									return 'rect_res selected';
								}
							}
						}) 
				}
			}

			labels = ['Organization', 'Project', 'Themes']
			// create y axis labels
			svg.select('#g_axis').selectAll('text')
					.data(labels)
					.enter()
					.append('text')
					.attr('x', paddingLeft)
					.attr('y', lineSpacing + dataHeight / 2)
					.text(function (d) {
						return d;
					})
					.attr('transform', function (d, i) {
						return 'translate(0,' + ((lineSpacing + dataHeight) * i) + ')';
					})
					.attr('class','ytitle');

			// create vertical grid
			svg.select('#g_axis').selectAll('line.vert_grid').data(xScale.ticks())
					.enter()
					.append('line')
					.attr({
						'class': 'vert_grid',
						'x1': function (d) {
							return xScale(d);
						},
						'x2': function (d) {
							return xScale(d);
						},
						'y1': 0,
						'y2': dataHeight * (noOfDatasets + 3) + lineSpacing * (noOfDatasets - 1) + paddingBottom
					});

			// create horizontal grid
			svg.select('#g_axis').selectAll('line.horz_grid').data(dataset)
					.enter()
					.append('line')
					.attr({
						'class': 'horz_grid',
						'x1': 0,
						'x2': width,
						'y1': function (d, i) {
							return ((lineSpacing + dataHeight) * i) + lineSpacing + dataHeight / 2;
						},
						'y2': function (d, i) {
							return ((lineSpacing + dataHeight) * i) + lineSpacing + dataHeight / 2;
						}
					});

			// create x axis
			svg.select('#g_axis').append('g')
					.attr('class', 'axis')
					.call(xAxis);

			var tickArr = xScale.ticks();
			var res_width = xScale(tickArr[1]) - xScale(tickArr[0]);
			var res_height = res_width * 9/16 * 2 + 10; // expecting icons to be 16:9 ratio
			var curr_decade = 0;
			var index_for_decade = 0;
			var max_index = 0; 

			function determine_y(d) {
				var decade = round_down(Math.floor(d.YEAR), 5);
				if (decade !== curr_decade) {
					curr_decade = decade;
					index_for_decade = 0;
				}
				else {
					index_for_decade += 1;
					if (index_for_decade > max_index) {
						max_index = index_for_decade;
					}
				}
				var y = (index_for_decade * res_height) + (((lineSpacing + dataHeight) * (noOfDatasets + 1)) + lineSpacing + dataHeight); 
				return y;      
			}

			var g_slices = svg.select('#g_slices');

			g_slices.selectAll('rect')
				.data(corpus)
				.enter()
				.append('rect')
				.attr({
					'class': 'rect_res not_selected',
					'x': function(d) {
						return xScale(parseYear.parse(round_down(d.YEAR, 5).toString()));
					},
					'y': function(d) {
						return determine_y(d);
					},
					'id': function(d) {
						return d._id.toString();
					},
					'width': res_width,
					'height': res_height,
				})
				.each(function(d) {
					var rect = document.getElementById(this.id);
					rect.style.fillOpacity = 1.0;
				})

				g_slices.selectAll('foreignObject').filter(function() {return this.getAttribute('class') == 'res'})
					.data(corpus)
					.enter()
					.append('foreignObject')
					.attr({
						'class': 'res',
						'x': function(d) {
							return xScale(parseYear.parse(round_down(d.YEAR, 5).toString())) + 4;
						},
						'y': function(d) {
							return determine_y(d) + res_height / 2;
						},
						'width': res_width - 8,
						'height': res_height - 8
					})
					.text(function(d) {
						return d.TITLE;
					});

				// image border
				g_slices.selectAll('rect').filter(function() {return this.getAttribute('class') == 'border'})
				.data(corpus)
				.enter()
				.append('rect')
				.attr({
					'class': 'border',
					'x': function(d) {
						return xScale(parseYear.parse(round_down(d.YEAR, 5).toString())) + 4;
					},
					'y': function(d) {
						return determine_y(d) + 6;
					},
					'width': '81px',
					'height': '46px',
					'fill': 'black'
				})

				g_slices.selectAll('image')
					.data(corpus)
					.enter()
					.append('image')
					.attr({
						'xlink:href': function(d, i) {
							return "/static/images/icons/" + d.ID + "-icon.jpg";
						},
						'x': function(d) {
							return xScale(parseYear.parse(round_down(d.YEAR, 5).toString())) + 4.5;
						},
						'y': function(d) {
							return determine_y(d) + 7;
						},
						'width': '80px',
						'height': '45px'
					})

				var g_icons = svg.select('#g_icons')
				g_icons.selectAll('image')
					.data(corpus)
					.enter()
					.append('image')
					.attr({
						'xlink:href': function(d, i) {
							if (d.TYPE === 'Video') return "/static/css/icons/Video.png";
						},
						'x': function(d) {
							return xScale(parseYear.parse(round_down(d.YEAR, 5).toString())) + 4.5;
						},
						'y': function(d) {
							return determine_y(d) + 4.5;
						},
						'width': '80px',
						'height': '45px'
					})

			// make y groups for different data series
			var g = svg.select('#g_data').selectAll('.g_data')
					.data(dataset.slice(startSet, endSet))
					.enter()
					.append('g')
					.attr('transform', function (d, i) {
						return 'translate(0,' + ((lineSpacing + dataHeight) * i) + ')';
					})
					.attr('class', 'dataset');

			// add data series
			g.selectAll('rect')
					.data(function(d) {
						return d.disp_data;
					})
					.enter()
					.append('rect')
					.attr('x', function (d) {
						return xScale(d[0]);
					})
					.attr('y', lineSpacing)
					.attr('width', function (d) {
						return (xScale(d[2]) - xScale(d[0]));
					})
					.attr('height', dataHeight)
					.attr('class', function (d) {
						if (d[1] === 1) {
							return 'rect_has_data';
						}
						else if (d[1] === 9) {
							return 'time_period';
						}
						return 'rect_has_no_data';
					})
					.on('click', function(d, i) {
						if (this.getAttribute('class') === 'time_period') {
							this.setAttribute('class', 'time_period_active');
						} else if (this.getAttribute('class') === 'time_period_active') {
							this.setAttribute('class', 'time_period');
						}
					})
					.on('mouseover', function (d, i) {
						highlight_res_in_period(d[0], d[2], true);
					})
					.on('mouseout', function (d) {
						highlight_res_in_period(d[0], d[2], false);
					});

				g.selectAll('rect')
					.each(function(d) {
						var matrix = this.getScreenCTM().translate(+this.getAttribute('x'), +this.getAttribute('y'));
						var width = this.getAttribute('width');
						d3.select('body').append('div')
						.attr('class', 'tooltip')
						.style('opacity', 0.9)
						.text(d[3])
						.style('width', width + 'px')
						.style('text-align', 'center')
						.style('left', function () {
							return window.pageXOffset + matrix.e + 'px';
						})
						.style('top', function () {
							return window.pageYOffset + matrix.f - 11 + 'px';
						})
						.style('height', dataHeight + 11 + 'px');	
					});

			var g_topics = svg.select('#g_topics').selectAll('.g_data')
					.data(_themes.slice(0, _themes.length))
					.enter()
					.append('g')
					.attr('transform', function (d, i) {
						return 'translate(0,' + (lineSpacing + (dataHeight * .6)*i) + ')';
					})
					.attr('class', 'dataset');

			g_topics.selectAll('rect')
					.data(function(d) {
						return d.disp_data;
					})
					.enter()
					.append('rect')
					.attr('x', function (d) {
						return xScale(d[0]);
					})
					.attr('y', (dataHeight + lineSpacing) * noOfDatasets)
					.attr('width', function (d) {
						return (xScale(d[2]) - xScale(d[0]));
					})
					.attr('height', dataHeight * .6)
					.attr('class', 'time_period')
					.on('click', function(d, i) {
						if (this.getAttribute('class') === 'time_period') {
							this.setAttribute('class', 'time_period_active');
							show_influenced_documents(d[3], 1, i, true);
						} else if (this.getAttribute('class') === 'time_period_active') {
							this.setAttribute('class', 'time_period');
							show_influenced_documents(d[3], 1, i, false);
							// svg.select('#g_slices').selectAll('rect').filter(function() { return this.getAttribute('class') == 'rect_res selected' })
							// 	.transition()
							// 	.duration(0)
							// 	.attr('class', 'rect_res not_selected');
						}
						div.transition()
								.duration(0)
								.style('opacity', 0.9);
					})
					.on('mouseover', function (d, i) {
						// highlight_res_in_period(d[0], d[2]);
						var matrix = this.getScreenCTM().translate(+this.getAttribute('x'), +this.getAttribute('y'));
						div.transition()
								.duration(0)
								.style('opacity', 0.9);
						div.html(function() {
							var output = '';
							var matches = d[3].match(/[^ 0.\d*\*](\w+)/g);
							for (var i = 0; i < matches.length; i++) {
								if (matches[i] in unstem) {
									matches[i] = unstem[matches[i]];
								}
								if (i !== matches.length - 1) output += matches[i] + ', ';
								else output += matches[i];
							}
							return output;
						})
						.style('left', function () {
							return window.pageXOffset + matrix.e + 'px';
						})
						.style('top', function () {
							return window.pageYOffset + matrix.f - 11 + 'px';
						})
						.style('height', dataHeight + 11 + 'px');
					})
					.on('mouseout', function (d) {
						if (this.getAttribute('class') === 'time_period') {
							div.transition()
									.duration(0)
									.style('opacity', 0);
						}
					});

			// create title
			if (drawTitle) {
				svg.select('#g_title')
						.append('text')
						.attr('x', paddingLeft)
						.attr('y', paddingTopHeading)
						.text('The Career of Douglas Engelbart')
						.attr('class', 'heading');
			}

			// create subtitle
			svg.select('#g_title')
					.append('text')
					.attr('x', paddingLeft)
					.attr('y', paddingTopHeading + 17)
					.text('from ' + moment(parseDate(startDate)).format('Y') + ' to '
							+ moment(parseDate(endDate)).format('Y'))
					.attr('class', 'subheading');

			// create legend
			var legend = svg.select('#g_title')
					.append('g')
					.attr('id', 'g_legend')
					.attr('transform', 'translate(0,-12)');

			legend.append('rect')
					.attr('x', width + margin.right - 150)
					.attr('y', paddingTopHeading)
					.attr('height', 15)
					.attr('width', 15)
					.attr('class', 'rect_has_data');

			legend.append('text')
					.attr('x', width + margin.right - 150 + 20)
					.attr('y', paddingTopHeading + 8.5)
					.text('Project')
					.attr('class', 'legend');

			legend.append('rect')
					.attr('x', width + margin.right - 150)
					.attr('y', paddingTopHeading + 17)
					.attr('height', 15)
					.attr('width', 15)
					.attr('class', 'rect_has_no_data');

			legend.append('text')
					.attr('x', width + margin.right - 150 + 20)
					.attr('y', paddingTopHeading + 8.5 + 15 + 2)
					.text('Organization')
					.attr('class', 'legend');

			var height = dataHeight * noOfDatasets + lineSpacing * noOfDatasets + (max_index + 1) * (res_height + lineSpacing);
			// var height = dataHeight * noOfDatasets + lineSpacing * noOfDatasets;
			d3.select('svg').attr('height', height + margin.top + margin.bottom);
		});
		
	}

	chart.width = function (_) {
		if (!arguments.length) return width;
		width = _;
		return chart;
	};

	chart.drawTitle = function (_) {
		if (!arguments.length) return drawTitle;
		drawTitle = _;
		return chart;
	};

	chart.maxDisplayDatasets = function (_) {
		if (!arguments.length) return maxDisplayDatasets;
		maxDisplayDatasets = _;
		return chart;
	};

	chart.curDisplayFirstDataset = function (_) {
		if (!arguments.length) return curDisplayFirstDataset;
		curDisplayFirstDataset = _;
		return chart;
	};

	chart.emphasizeYearTicks = function (_) {
		if (!arguments.length) return emphasizeYearTicks;
		emphasizeYearTicks = _;
		return chart;
	};

	return chart;
}
