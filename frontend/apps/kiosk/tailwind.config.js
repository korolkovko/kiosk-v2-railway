/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    screens: {
      mq900: {
        raw: "screen and (max-width: 900px)",
      },
      mq450: {
        raw: "screen and (max-width: 450px)",
      },
    },
    extend: {
      colors: {
        "Hover-stroke": "#c6b9ff",
      },
    },
  },
  corePlugins: {
    preflight: true,
  },
};
