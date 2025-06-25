# VHSL Map Website Documentation

## Overview
The Virginia High School League (VHSL) Map Website is an interactive web application that visualizes all VHSL schools across Virginia, organized by class/size, region, and district. The application allows users to explore, filter, and search for schools on an interactive map.

## Features
- **Interactive Map**: Displays all VHSL schools with color-coded markers based on class
- **Filtering System**: Filter schools by class (1-6), region (A-D), or district
- **School Search**: Quickly find specific schools by name
- **Detailed Information**: Click on any school to view its classification details
- **Mobile Responsive**: Fully functional on both desktop and mobile devices
- **Dismissible Sidebar**: On mobile devices, the sidebar can be opened and closed as needed

## Technical Implementation
- **Frontend Framework**: Built with Vite for modern, fast web development
- **Mapping Library**: OpenLayers for advanced mapping capabilities
- **Data Source**: GeoJSON files are fetched directly from the GitHub repository
  using the `raw.githubusercontent.com` service. This keeps the application
  lightweight and decouples the data from the deployed code.
- **Performance Optimizations**: 
  - Style caching for faster rendering
  - Batch DOM updates for smoother UI
  - Debounced event handlers for better responsiveness
  - Tile preloading for faster map navigation

## Directory Structure
```
vhsl-map-project/
├── data/                  # Raw data files
│   ├── geojson/           # GeoJSON data files
│   │   ├── classes/       # Class-specific GeoJSON files
│   │   └── ...
├── public/                # Public assets for deployment
├── src/                   # Source code
│   ├── assets/            # Static assets (images, etc.)
│   ├── js/                # JavaScript files
│   │   └── main.js        # Main application logic
│   ├── styles/            # CSS styles
│   │   └── main.css       # Main stylesheet
│   └── index.html         # Main HTML file
├── dist/                  # Built files (generated)
├── package.json           # Project configuration
└── vite.config.js         # Vite configuration
```

## Data Structure
The application uses several data sources:
1. **School GeoJSON**: Contains geographic coordinates and basic information for all schools
2. **School Lookup**: JSON file mapping school names to their class, region, and district information
3. **Enriched Data**: Combined data with complete classification information for all schools

## Development
To continue development:
1. Clone the repository
2. Run `npm install` to install dependencies
3. Run `npm run dev` to start the development server
4. Make changes to the source files
5. Run `npm run build` to build for production

## Deployment
The website is deployed at: https://ahvnjexf.manus.space

To deploy updates:
1. Build the project with `npm run build`
2. Deploy the contents of the `dist` directory to your web server. The
   application will retrieve GeoJSON data from GitHub at runtime, so no data
   files need to be served alongside the build.

## Future Enhancements
Potential future enhancements include:
- Adding geographical boundaries for regions and districts
- Implementing additional filtering options
- Adding historical data and statistics for schools
- Enhancing the UI with additional visualizations

## Contact
For questions or support, please contact the VHSL administration.
