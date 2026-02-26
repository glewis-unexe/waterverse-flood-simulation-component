//let server_url = 'http://127.0.0.1:9999/';
let server_url = '/';

class TestDataComponent extends HTMLComponent{
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
        this.content.style.height = "calc(100vh - 50px)";
        this.content.style.backgroundColor = this.bg_colour;
        this.content.style.overflowY = 'scroll';
        this.content.style.overflowX = 'hidden';
        this.root.appendChild(this.content);

        let top = '0px';
        let content_root = this.content;

        this.elements = {};

        let params = {};

        let cmd = server_url + 'get_scenarios/';

        axios.get(cmd, {params: params}).then(response => {
            if (response.status === 200) {
                var scenarios = response.data;
                //go to the server and get the sdg options

                for (let i = 0; i < scenarios.length; i++) {

                    let row = document.createElement('row');
                    row.className = "row text-center";
                    row.style.width = '40vw';
                    row.style.marginLeft = '30vw';
                    row.style.marginRight = '70vw';
                    content_root.appendChild(row);
                    let button = document.createElement('button');
                    button.className = "mt-5 btn btn-primary text-center";
                    button.type = "button";
                    button.style.width = '100%';
                    button.style.height = '10vh';
                    button.id = "button-" + i.toString();
                    button.innerText = scenarios[i]['print_name'];

                    //button on press, send sdg name back to server and start simulating ....
                    button.onclick = function () {
                        let cmd = server_url + 'run_scenario/' + scenarios[i]['id'];
                        axios.put(cmd);
                    };

                    row.appendChild(button);
                }

                for (let i = 0; i < 5; i++) {
                    content_root.appendChild(document.createElement('br'));
                }
            } else {
            }
        });
    }
}

class LoggingComponent extends HTMLComponent{
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

        let top = '0px';
        let content_root = this.content;

        this.elements = {};
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
        this.components['Create Test Data'] = new TestDataComponent();
        this.components['Logging'] = new LoggingComponent();

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
        this.nav_selector.set_current_item('Create Test Data');
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


function app_init(root, mapbox_id) {

  mapboxgl.accessToken = mapbox_id;

  let content_root = document.createElement('div');
  content_root.style.left = '0px';
  content_root.style.margin = '0';
  content_root.style.padding = '0';
  content_root.id = 'my_app_root';
  content_root.overflowY = 'hidden';

  content_root.style.bottom = '0px';
  content_root.style.backgroundColor = '#ff0000';

  root.appendChild(content_root);

  let app = new AppScreen();
  app.oneTimeInit(content_root);
  app.onShow(content_root);
}
