# UniNest Housing Web Application

A modern web application for managing and finding student housing properties.

## Features

- Property listing and management
- Landlord profile management
- Property search and filtering
- Interactive map integration
- Image upload and management
- Responsive design
- User authentication and authorization

## Prerequisites

Before you begin, ensure you have installed:
- Node.js (v16.0.0 or higher)
- npm (v8.0.0 or higher)

## Environment Setup

1. Create a `.env` file in the root directory with the following variables:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd frontend/housing-web
```

2. Install dependencies:
```bash
npm install
```

## Development

To start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Building for Production

To create a production build:
```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
housing-web/
├── public/          # Static files
├── src/
│   ├── api/        # API integration
│   ├── components/ # Reusable components
│   ├── pages/      # Page components
│   ├── styles/     # Global styles
│   └── utils/      # Utility functions
├── .env            # Environment variables
└── package.json    # Project dependencies
```

## Dependencies

### Main Dependencies
- React 18
- React Router DOM
- @react-google-maps/api
- Axios
- TailwindCSS
- React Hot Toast
- React Dropzone

### Development Dependencies
- Vite
- ESLint
- PostCSS
- Autoprefixer

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Browser Support

The application supports the following browsers:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License.
