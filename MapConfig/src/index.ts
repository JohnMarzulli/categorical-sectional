// index.js
// @ts-check

import path from "path";
import request, { CoreOptions } from "request";
import dateformat from "dateformat";
import express from "express";
import bodyParser from "body-parser";
import expressHandlebars from "express-handlebars";
import ip from "ip";

const isPi = require(`detect-rpi`);

/**
 * Returns the address of the WeatherMap host.
 *
 * @returns {string}
 */
function getAddress(): string {
  return ip.address();
}

/**
 * Get the port that the WeatherMap is running on.
 *
 * @returns {number}
 */
function getWebServerPort(): number {
  if (isPi()) {
    return 80;
  }

  return 3000;
}

function getWeatherMapRestUri(): string {
  return `http://${getAddress()}:8080`;
}

console.log(`Assuming WeatherMap can be contacted at ${getWeatherMapRestUri()}`);
console.log(`Starting Web/NodeJs on ${getWebServerPort()}`);


/**
 * Updates the hash/dictionary that will be sent in a PUT to the WeatherMap.
 *
 * @param {*} hash
 * @param {string} key
 * @param {*} value
 * @returns
 */
function mergeIntoHash(
  hash: any,
  key: string,
  value: any
): any {
  if (hash == undefined) {
    hash = {};
  }

  if (value != undefined
    && value != null
    && !isNaN(value)) {
    hash[key] = value;
  }

  return hash;
}

const app = express();

function getWeatherMapRequest(
  requestDirectory: string,
): any {
  return `${getWeatherMapRestUri()}/${requestDirectory}`;
}

function getWeatherMapUrl(
  payload?: any
): any {
  return getWeatherMapRequest("settings");
}

function getNumber(
  inputString: string
): number {
  try {
    return Number(inputString);
  } catch (error) {
    return 0;
  }
}

function getBoolean(
  inputString: string
): boolean {
  try {
    if (inputString == undefined) {
      return false;
    }

    inputString = inputString.toLowerCase();

    return inputString == "true" || inputString == "on";
  } catch (error) {
    return false;
  }
}

app.engine(
  ".hbs",
  expressHandlebars({
    defaultLayout: "main",
    extname: ".hbs",
    layoutsDir: path.join(__dirname, "../views/layouts"),
    helpers: {
      ifeq: function (a: any, b: any, options: any) {
        if (a == b) { return options.fn(this); }
        return options.inverse(this);
      }
    }
  })
);
app.set("view engine", ".hbs");
app.set("views", path.join(__dirname, "../views"));

function handleJsonResponse(
  restRes: request.Response,
  resolve: any,
  reject: any
) {
  let responseBody: string = '';
  if (restRes.statusCode >= 200 && restRes.statusCode < 300) {
    restRes.on("data", function (data) {
      responseBody += data;
    });
    restRes.on("end", () => {
      console.log(`BODY: ${responseBody}`);

      var firstLevelParse = JSON.parse(responseBody);

      if (typeof (firstLevelParse) === 'string') {
        resolve(JSON.parse(firstLevelParse));
      } else {
        resolve(firstLevelParse);
      }
    });
  } else {
    reject({ error: restRes.statusCode });
  }
}

function getWeatherMapView() {
  return new Promise((resolve, reject) => {
    request
      .get(getWeatherMapRequest("view"))
      .on("error", function (err) {
        console.log(err);
        reject(err.message);
      })
      .on("response", function (response) {
        handleJsonResponse(response, resolve, reject);
      });
  });
}

function getWeatherMapConfig() {
  return new Promise((resolve, reject) => {
    request
      .get(getWeatherMapUrl())
      .on("error", function (err) {
        console.log(err);
        reject(err.message);
      })
      .on("response", function (response) {
        handleJsonResponse(response, resolve, reject);
      });
  });
}

function changeView(
  view: string
) {
  return new Promise((resolve, reject) => {
    request
      .get(`${getWeatherMapRestUri()}/view/${view}`)
      .on("error", function (err) {
        console.log(err);
        reject(err.message);
      })
      .on("response", function (response) {
        resolve(response);
      });
  });
}

/**
 * Signals to move to the next view
 *
 * @returns the JSON result from the call
 */
function nextView() {
  return changeView("next");
}

/**
 * Signals to move to the next view
 *
 * @returns the JSON result from the call
 */
function previousView() {
  return changeView("previous");
}

function putConfig(
  url: string,
  updateHash: any
) {
  return new Promise(function (resolve, reject) {
    request.put(
      url,
      { json: updateHash },
      function optionalCallback(
        err,
        httpResponse,
        body
      ) {
        if (err) {
          reject(err);
          return console.error('upload failed:', err);
        }
        console.log('Upload successful!  Server responded with:', body);
      }).on("end", () => {
        resolve();
      });
  });
}

function postWeatherMapConfig(
  updateHash: any
) {
  putConfig(getWeatherMapUrl(), updateHash);
}

function renderRefused(
  response: any,
  error: string
) {
  console.log("Render");

  response.render("refused", {
    error: error,
    time: dateformat(Date.now(), "dd-mm-yy hh:MM:ss TT")
  });
}

function renderPage(
  response: any,
  jsonConfig: any,
  page = "config"
) {
  console.log("Render");
  response.render(page, {
    time: dateformat(Date.now(), "dd-mm-yy hh:MM:ss TT"),
    configJson: jsonConfig
  });
}

function mapViewRender(
  response: any
) {
  return getWeatherMapView()
    .then(function (jsonConfig) {
      renderPage(response, jsonConfig, "views");
    })
    .catch(function (error) {
      renderRefused(response, error);
    });
}

app.get("/", (request, response) => {
  mapViewRender(response);
});

app.get("/views/previous", (request, response) => {
  previousView()
    .then(function (jsonConfig) {
      response.redirect('/');
    })
    .catch(function (error) {
      renderRefused(response, error);
    });
});

app.get("/views/next", (request, response) => {
  nextView().then(function (jsonConfig) {
    response.redirect('/');
  })
    .catch(function (error) {
      renderRefused(response, error);
    });
});

app.get("/config", (request, response) => {
  getWeatherMapConfig()
    .then(function (jsonConfig) {
      renderPage(response, jsonConfig, "config");
    })
    .catch(function (error) {
      renderRefused(response, error);
    });
});

app.use(express.static(path.join(__dirname, "../public")));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.post("/", function (request, response) {
  var updateHash = mergeIntoHash({}, "mode", request.body.mode);
  updateHash = mergeIntoHash(
    updateHash,
    "pixel_count",
    getNumber(request.body.pixel_count)
  );
  updateHash = mergeIntoHash(
    updateHash,
    "spi_device",
    getNumber(request.body.spi_device)
  );
  updateHash = mergeIntoHash(
    updateHash,
    "spi_port",
    getNumber(request.body.spi_port)
  );
  updateHash = mergeIntoHash(
    updateHash,
    "airports_file",
    request.body.airports_file
  );
  updateHash = mergeIntoHash(
    updateHash,
    "blink_old_stations",
    getBoolean(request.body.blink_old_stations)
  );
  updateHash = mergeIntoHash(
    updateHash,
    "blink_lightning",
    getBoolean(request.body.blink_lightning)
  );
  updateHash = mergeIntoHash(
    updateHash,
    "night_lights",
    getBoolean(request.body.night_lights)
  );
  updateHash = mergeIntoHash(
    updateHash,
    "night_populated_yellow",
    getBoolean(request.body.night_populated_yellow)
  );
  updateHash = mergeIntoHash(
    updateHash,
    "night_category_proportion",
    getNumber(request.body.night_category_proportion)
  );
  updateHash = mergeIntoHash(
    updateHash,
    "brightness_proportion",
    getNumber(request.body.brightness_proportion)
  );
  updateHash = mergeIntoHash(
    updateHash,
    "visualizer",
    getNumber(request.body.visualizer)
  );

  postWeatherMapConfig(updateHash);
  renderPage(response, updateHash);
});

app.use(function (request, response) {
  response.status(404);
  response.render("404");
});

app.listen(getWebServerPort());
