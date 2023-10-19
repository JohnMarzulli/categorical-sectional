"use strict";
// index.js
// @ts-check
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
var path_1 = __importDefault(require("path"));
var request_1 = __importDefault(require("request"));
var dateformat_1 = __importDefault(require("dateformat"));
var express_1 = __importDefault(require("express"));
var body_parser_1 = __importDefault(require("body-parser"));
var express_handlebars_1 = __importDefault(require("express-handlebars"));
var ip_1 = __importDefault(require("ip"));
var isPi = require("detect-rpi");
/**
 * Returns the address of the WeatherMap host.
 *
 * @returns {string}
 */
function getAddress() {
    return ip_1.default.address();
}
/**
 * Get the port that the WeatherMap is running on.
 *
 * @returns {number}
 */
function getWebServerPort() {
    if (isPi()) {
        return 80;
    }
    return 3000;
}
function getWeatherMapRestUri() {
    return "http://" + getAddress() + ":8080";
}
console.log("Assuming WeatherMap can be contacted at " + getWeatherMapRestUri());
console.log("Starting Web/NodeJs on " + getWebServerPort());
/**
 * Updates the hash/dictionary that will be sent in a PUT to the WeatherMap.
 *
 * @param {*} hash
 * @param {string} key
 * @param {*} value
 * @returns
 */
function mergeIntoHash(hash, key, value) {
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
var app = express_1.default();
function getWeatherMapRequest(requestDirectory) {
    return getWeatherMapRestUri() + "/" + requestDirectory;
}
function getWeatherMapUrl(payload) {
    return getWeatherMapRequest("settings");
}
function getNumber(inputString) {
    try {
        return Number(inputString);
    }
    catch (error) {
        return 0;
    }
}
function getBoolean(inputString) {
    try {
        if (inputString == undefined) {
            return false;
        }
        inputString = inputString.toLowerCase();
        return inputString == "true" || inputString == "on";
    }
    catch (error) {
        return false;
    }
}
app.engine(".hbs", express_handlebars_1.default({
    defaultLayout: "main",
    extname: ".hbs",
    layoutsDir: path_1.default.join(__dirname, "../views/layouts"),
    helpers: {
        ifeq: function (a, b, options) {
            if (a == b) {
                return options.fn(this);
            }
            return options.inverse(this);
        }
    }
}));
app.set("view engine", ".hbs");
app.set("views", path_1.default.join(__dirname, "../views"));
function handleJsonResponse(restRes, resolve, reject) {
    var responseBody = '';
    if (restRes.statusCode >= 200 && restRes.statusCode < 300) {
        restRes.on("data", function (data) {
            responseBody += data;
        });
        restRes.on("end", function () {
            console.log("BODY: " + responseBody);
            var firstLevelParse = JSON.parse(responseBody);
            if (typeof (firstLevelParse) === 'string') {
                resolve(JSON.parse(firstLevelParse));
            }
            else {
                resolve(firstLevelParse);
            }
        });
    }
    else {
        reject({ error: restRes.statusCode });
    }
}
function getWeatherMapView() {
    return new Promise(function (resolve, reject) {
        request_1.default
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
    return new Promise(function (resolve, reject) {
        request_1.default
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
function changeView(view) {
    return new Promise(function (resolve, reject) {
        request_1.default
            .get(getWeatherMapRestUri() + "/view/" + view)
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
function putConfig(url, updateHash) {
    return new Promise(function (resolve, reject) {
        request_1.default.put(url, { json: updateHash }, function optionalCallback(err, httpResponse, body) {
            if (err) {
                reject(err);
                return console.error('upload failed:', err);
            }
            console.log('Upload successful!  Server responded with:', body);
        }).on("end", function () {
            resolve();
        });
    });
}
function postWeatherMapConfig(updateHash) {
    putConfig(getWeatherMapUrl(), updateHash);
}
function renderRefused(response, error) {
    console.log("Render");
    response.render("refused", {
        error: error,
        time: dateformat_1.default(Date.now(), "dd-mm-yy hh:MM:ss TT")
    });
}
function renderPage(response, jsonConfig, page) {
    if (page === void 0) { page = "config"; }
    console.log("Render");
    response.render(page, {
        time: dateformat_1.default(Date.now(), "dd-mm-yy hh:MM:ss TT"),
        configJson: jsonConfig
    });
}
function mapViewRender(response) {
    return getWeatherMapView()
        .then(function (jsonConfig) {
        renderPage(response, jsonConfig, "views");
    })
        .catch(function (error) {
        renderRefused(response, error);
    });
}
app.get("/", function (request, response) {
    mapViewRender(response);
});
app.get("/views/previous", function (request, response) {
    previousView()
        .then(function (jsonConfig) {
        response.redirect('/');
    })
        .catch(function (error) {
        renderRefused(response, error);
    });
});
app.get("/views/next", function (request, response) {
    nextView().then(function (jsonConfig) {
        response.redirect('/');
    })
        .catch(function (error) {
        renderRefused(response, error);
    });
});
app.get("/config", function (request, response) {
    getWeatherMapConfig()
        .then(function (jsonConfig) {
        renderPage(response, jsonConfig, "config");
    })
        .catch(function (error) {
        renderRefused(response, error);
    });
});
app.use(express_1.default.static(path_1.default.join(__dirname, "../public")));
app.use(body_parser_1.default.json());
app.use(body_parser_1.default.urlencoded({ extended: true }));
app.post("/", function (request, response) {
    var updateHash = mergeIntoHash({}, "mode", request.body.mode);
    updateHash = mergeIntoHash(updateHash, "pixel_count", getNumber(request.body.pixel_count));
    updateHash = mergeIntoHash(updateHash, "spi_device", getNumber(request.body.spi_device));
    updateHash = mergeIntoHash(updateHash, "spi_port", getNumber(request.body.spi_port));
    updateHash = mergeIntoHash(updateHash, "airports_file", request.body.airports_file);
    updateHash = mergeIntoHash(updateHash, "blink_old_stations", getBoolean(request.body.blink_old_stations));
    updateHash = mergeIntoHash(updateHash, "blink_lightning", getBoolean(request.body.night_lights));
    updateHash = mergeIntoHash(updateHash, "night_lights", getBoolean(request.body.night_lights));
    updateHash = mergeIntoHash(updateHash, "night_populated_yellow", getBoolean(request.body.night_populated_yellow));
    updateHash = mergeIntoHash(updateHash, "night_category_proportion", getNumber(request.body.night_category_proportion));
    updateHash = mergeIntoHash(updateHash, "brightness_proportion", getNumber(request.body.brightness_proportion));
    updateHash = mergeIntoHash(updateHash, "visualizer", getNumber(request.body.visualizer));
    postWeatherMapConfig(updateHash);
    renderPage(response, updateHash);
});
app.use(function (request, response) {
    response.status(404);
    response.render("404");
});
app.listen(getWebServerPort());
//# sourceMappingURL=index.js.map