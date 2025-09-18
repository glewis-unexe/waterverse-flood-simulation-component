mapboxgl.accessToken = 'pk.eyJ1IjoiZ2F6dGFzdGljIiwiYSI6ImNrYzA4Y2c4NjFoYnIyeHRicmZuaTgyMGQifQ.fkkbIOCwq4j70CqNeiBGcA';
//let server_url = 'http://localhost:9999/flooding';
let server_url = '/flooding/';

function getFilenameAndExtension(pathfilename){

  var filenameextension = pathfilename.replace(/^.*[\\\/]/, '');
  var filename = filenameextension.substring(0, filenameextension.lastIndexOf('.'));
  var ext = filenameextension.split('.').pop();

  return [filename, ext];
}

class FloodMapComponent  extends MapboxComponent {
    constructor() {
        super();

        this.center = [8.76, 51.63];
        this.zoom = 15;
        this.bearing = 0;
        this.pitch = 0;

        this.popup = undefined;

        this.current_layer_name = '';
        this.layer_data = {};
    }

    oneTimeInit() {
        super.oneTimeInit();
    }

    onShow(parent) {
        super.onShow(parent);

        let top = '70px';
        let content_root = this.content;

        this.elements['map.flood.legend'] = new Mapbox_LegendList(content_root,{
            'left': '1vw',
            'top': '200px',
        });

        this.elements['map.sources.dropdown'] = new Mapbox_dropdown(content_root, {
            'left': 'max(470px,34vw)',
            'top': top,
            'width': 'max(180px, 10vw)',
        });


        this.on_mouse_move = function(e){

            this.fill_map_pos_textbox(e);

            let loc = this.map.getCenter();
            let features = undefined;

            if (e !== undefined) {
                features = this.map.queryRenderedFeatures(e.point);
                loc = e.lngLat;
            }

            let text = '';

            if (features !== undefined) {
                for (let i = 0; i < features.length; i++) {
                    if (features[i].layer.id === this.current_layer_name) {
                        if ('depth' in features[i].properties) {
                            text = 'Depth: ' + features[i].properties['depth'].toFixed(2) + 'm';
                        }
                        text += '\n';
                    }
                }
            }

            if (text === ''){
                text = 'Depth: ' + 'n/a';
            }

            if ('map.info.textbox' in this.elements) {
                this.elements['map.info.textbox'].set_text(text);
            }
        };
    }

    on_style_load(){
        super.on_style_load();

        this.popup = new mapboxgl.Popup({
            offset: 25,
            maxWidth: 1200,
            closeButton: false,
            closeOnClick: true
        });


        this.layer_data = {};

        //load data
        let params = {};

        let cmd = server_url + 'get_flood_data';

        axios.get(cmd, {params: params}).then(response => {
            if (response.status === 200) {

                var record = response.data;

                try {
                    if (this.map) {
                        if ('color_key' in record){

                            let temp = [];
                            for (let i = 0; i < record['color_key'].length; i++) {

                                let current = record['color_key'][i];

                                temp.push({
                                    text: current.text,
                                    color: current.color,
                                    id: i
                                });
                            }

                            if ('map.flood.legend' in this.elements) {
                                this.elements['map.flood.legend'].init(temp);
                            }
                        }

                        let temp = [];
                        temp.push({name: 'none', layer: undefined});

                        let print_timestamp = '';

                        if ('timestamp_print' in record){
                            print_timestamp = record['timestamp_print'];
                        }

                        if ('geojson' in record){
                            for (let i = 0; i < record['geojson'].length; i++) {
                                let current = record['geojson'][i];
                                let layer_name = print_timestamp + ' ' + current.type + ' floodmap';
                                let layer = new MapboxLayer_Geojson(layer_name, current.url, false);

                                layer.paint_data = {
                                    'fill-color': ['get', 'color'],
                                    'fill-opacity': 0.7,
                                };

                                layer.init(this.map, this.current_layer_name === layer_name);
                                this.layer_data[layer.layer_name] = layer;
                                temp.push({name: layer.layer_name, layer:layer});
                            }
                        }

                        if ('image' in record) {
                            for (let i = 0; i < record['image'].length; i++) {
                                let current = record['image'][i];
                                let layer_name = 'Reference ' + current.type;
                                let layer = new MapboxLayer_Raster(layer_name, current.url, record['rect']);
                                layer.init(this.map,this.current_layer_name === layer_name);
                                this.layer_data[layer.layer_name] = layer;
                                temp.push({name: layer.layer_name, layer: layer});
                            }
                        }

                        let self = this;
                        this.elements['map.sources.dropdown'].reset();

                        for (let i = 0; i < temp.length; i++) {

                            let item = temp[i];

                            if (i == 0) {
                                if ('map.sources.dropdown' in this.elements) {
                                    this.elements['map.sources.dropdown'].set_button_text('Source Layers');
                                }
                            }

                            let menu_item = new Mapbox_dropdown_item2(this.elements['map.sources.dropdown'], function (d) {
                                self.set_current_layer(item);
                            });
                            menu_item.set_name(item['name']);
                            this.elements['map.sources.dropdown'].append_menu_option(menu_item);
                        }

                        for (let i = 0; i < temp.length; i++) {

                            let item = temp[i];

                            if (item.name === this.current_layer_name){
                                this.elements['map.sources.dropdown'].set_button_text(item['name']);
                            }
                        }
                    }
                } catch (e) {
                    console.log(e);
                }
            }
        }).catch(function (error) {
            if (error.response) {
                console.log(arguments, 'Error:' + cmd + ' ' + error.response.data);
            }
        });
    }

    get_display_name_for_layer(item){

        if(item.name === 'none'){
            return 'None';
        }

        let name = getFilenameAndExtension(item.layer.url);

        if (item.layer instanceof MapboxLayer_Raster){
            return 'Image ' + name[0].replace('_', ' ').replace('T', ' ').replace('Z', ' ');
        }

        if (item.layer instanceof MapboxLayer_Geojson){
            return 'Geojson ' + name[0].replace('_', ' ').replace('T', ' ').replace('Z', ' ');
        }

        return 'Undefined';
    }

    set_current_layer(item) {

        for (const [key, value] of Object.entries(this.layer_data)) {
            value.set_visibility(false);
        }

        this.current_layer_name = item.name; //actual layer name, not the display name :S

        item['layer'].set_visibility(true);

        this.elements['map.sources.dropdown'].set_button_text(item['name']);
    }
}

class TrafficLightComponent extends HTMLComponent{
    constructor() {
        super();
        this.elements = {};
    }
    oneTimeInit() {
        super.oneTimeInit();
    }

    onShow(parent) {
        super.onShow(parent);

        this.content = document.createElement('div');
        this.content.id = this.get_ID();
        this.content.className = 'Square';
        this.content.style.width = "100%";
        this.content.style.height = "100vh";
        this.content.style.backgroundColor = this.bg_colour;
        this.root.appendChild(this.content);

        let top = '70px';
        let content_root = this.content;

        this.elements = {};

        this.elements['current.textbox'] = new Mapbox_Textbox(content_root, {
            'left': '1vw',
            'top': '100px',
            'width': 'calc(100% - 2vw)',
            'height': '25%',
        });

        this.elements['current.textbox'].set_bg("#7f7f7f");

        this.elements['nowcast.textbox'] = new Mapbox_Textbox(content_root, {
            'left': '1vw',
            'top': 'calc(100px + 30%)',
            'width': 'calc(100% - 2vw)',
            'height': '25%',
        });

        this.elements['nowcast.textbox'].set_bg("#7f7f7f");

        this.elements['forecast.textbox'] = new Mapbox_Textbox(content_root, {
            'left': '1vw',
            'top': 'calc(100px + 60%)',
            'width': 'calc(100% - 2vw)',
            'height': '25%',
        });

        this.elements['forecast.textbox'].set_bg("#7f7f7f");

        let params = {};

        let cmd = server_url + 'get_flood_data/';

        axios.get(cmd, {params: params}).then(response => {
            if (response.status === 200) {

                var record = response.data;

                let headings = {
                    'current' : 'Over the last couple of days',
                    'nowcast' : 'Over the next couple of hours',
                    'forecast' : 'Over the next couple of days',
                };

                if ('traffic_lights' in record) {
                    let labels = ['current','nowcast','forecast'];

                    for(let i=0;i<labels.length;i++) {
                        let label =labels[i];
                        if (record['traffic_lights'][label] === 'green') {
                            this.elements[label + '.textbox'].set_bg("#46f346");
                        }

                        if (record['traffic_lights'][label] === 'amber') {
                            this.elements[label + '.textbox'].set_bg("#fdc34b");
                        }

                        if (record['traffic_lights'][label] === 'red') {
                            this.elements[label+'.textbox'].set_bg("#ff446a");
                        }

                        //this.elements[label + '.textbox'].set_innerHTML('<h2 style="text-align:center;"'+ headings[label]+'</h2>' + '<h4></h4>' + record['traffic_lights']['text'][label]);
                        if ('traffic_lights' in record && 'text' in record['traffic_lights']) {
                            this.elements[label + '.textbox'].set_innerHTML('<h2 style="text-align: center;">' + headings[label] + '</h2>' + '<h4></h4>' + record['traffic_lights']['text'][label]);
                        }else{
                            this.elements[label+'.textbox'].set_bg("#7f7f7f");
                            this.elements[label + '.textbox'].set_innerHTML('<h2 style="text-align: center;">' + headings[label] + '</h2>' + '<h4></h4>' + 'No data at this time');
                        }

                    }
                }
            }
        });
    }
}


class AppScreen extends Screen_base
{
    constructor(props) {
        super(props);

        this.components = {};
    }

    oneTimeInit(parent) {
        super.oneTimeInit(parent);


        this.data = {};

        this.components = {};
        this.components['Map View'] = new FloodMapComponent();
        this.components['Traffic Lights'] = new TrafficLightComponent();
        //this.components['SDG'] = new EttelnSDGComponent();

        for (const [key, component] of Object.entries(this.components)) {
            component.oneTimeInit();
        }

        this.nav_selector = new NavPills(this);
        this.nav_selector.labels = Object.keys(this.components);
        this.nav_selector.oneTimeInit(this.content_root);
    }

    onShow(parent) {
        super.onShow(parent);

        this.content_root = document.createElement('div');
        this.content_root.id = 'table_root';
        this.content_root.style.backgroundColor = "#ffffff";
        this.content_root.style.width = "100%";
        this.content_root.style.overflowY = 'scroll';
        this.content_root.style.overflowY = 'hidden';
        this.content_root.style.overflowX = 'hidden';
        this.content_root.style.top = '14px';
        this.content_root.style.bottom = '0px';
        this.content_root.style.position = 'absolute';

        this.root.appendChild(this.content_root);

        this.nav_selector.onShow(this.content_root);
        this.nav_selector.set_current_item('Traffic Lights');
    }

    input_handler(src, item_id){

        if (src.previous_option != ''){
            this.components[src.previous_option].removeFromDOM();
        }

        if(item_id in this.components) {
            this.components[item_id].onShow(this.content_root);
        }
    }
}

let app = new AppScreen();

function app_init(root) {
  let content_root = document.createElement('div');
  content_root.style.left = '0px';
  content_root.style.margin = '0';
  content_root.style.padding = '0';
  content_root.id = 'my_app_root';
  content_root.overflowY = 'hidden';

  content_root.style.bottom = '0px';
  content_root.style.backgroundColor = '#ff0000';

  root.appendChild(content_root);

  app.oneTimeInit(content_root);
  app.onShow(content_root);
}