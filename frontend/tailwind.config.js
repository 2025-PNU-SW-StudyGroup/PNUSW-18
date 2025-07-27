/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        main: '#4DDDBD',
        gray2: '#EDEDED',
        gray3: '#C3C3C3',
        gray5: '#9B9B9B',
        gray6: '#565958',
        black: '#1B1B1B',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
