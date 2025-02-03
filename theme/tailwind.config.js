const path = require('path');

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './static_src/src/**/*.{html,js}',
    '../blog/templates/**/*.html',
    '../blog/static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        'navy-blue': '#1a365d',
        'secondary-color': '#4299e1',  // Adding from old CSS
        'accent-color': '#f56565',     // Adding from old CSS
        'success-color': '#4CAF50',    // Adding from old CSS
        'text-color': '#2d3748',       // Adding from old CSS
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),  // For better form styling
  ],
} 