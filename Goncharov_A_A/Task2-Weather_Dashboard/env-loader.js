window.envLoader = (function () {
  const ENV_PATH = "./.env";
  let cached;

  async function load() {
    if (cached) {
      return cached;
    }
    try {
      const response = await fetch(ENV_PATH, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Failed to fetch env file with status ${response.status}`);
      }
      const text = await response.text();
      cached = parse(text);
    } catch (error) {
      console.warn("env-loader: unable to load .env", error);
      cached = {};
    }
    return cached;
  }

  function parse(raw) {
    return raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#"))
      .reduce((acc, line) => {
        const eqIndex = line.indexOf("=");
        if (eqIndex === -1) {
          return acc;
        }
        const key = line.slice(0, eqIndex).trim();
        const value = line.slice(eqIndex + 1).trim();
        if (!key) {
          return acc;
        }
        if (key === "OPEN_WEATHER_KEY") {
          acc.apiKey = value;
        }
        return acc;
      }, {});
  }

  return { load };
})();
