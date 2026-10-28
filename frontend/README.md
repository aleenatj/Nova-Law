# Nova Platform Frontend

A modern, responsive React application built with TypeScript, Tailwind CSS, and Vite.

## 🚀 Features

- **Modern React 18** with TypeScript
- **Tailwind CSS** for styling
- **Vite** for fast development and building
- **Form validation** with React Hook Form and Zod
- **Responsive design** for all devices
- **Component-based architecture** for maintainability

## 📁 Project Structure

```
client/
├── public/                 # Static assets served directly
│   └── index.html
├── src/
│   ├── assets/            # Images, fonts, icons
│   ├── components/        # Shared reusable UI components
│   │   └── Button/
│   │       ├── v1/
│   │       │   └── Button.tsx
│   │       └── v2/
│   │           └── Button.tsx
│   ├── features/          # Feature/domain specific logic and UI
│   │   ├── user/
│   │   │   ├── components/    # Feature scoped components
│   │   │   ├── hooks/
│   │   │   ├── api.ts
│   │   │   └── UserPage.tsx
│   │   └── product/
│   ├── hooks/             # App wide custom hooks
│   ├── contexts/          # React context providers
│   ├── lib/               # Wrappers for third party libraries
│   ├── utils/             # Utility functions/helpers
│   ├── pages/             # Top-level route components
│   ├── App.tsx
│   ├── main.tsx
│   └── styles/            # Global and theme styles
├── tsconfig.json
├── vite.config.ts
├── package.json
└── README.md
```

## 🛠️ Tech Stack

- **Frontend Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Form Management**: React Hook Form
- **Validation**: Zod
- **UI Components**: Custom components with Tailwind CSS

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nova-platform-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to `http://localhost:5000`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - Type check with TypeScript

## 🎨 Customization

### Colors and Theme

The application uses CSS custom properties for theming. You can customize colors in `src/index.css`:

```css
:root {
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  /* ... more variables */
}
```

### Tailwind Configuration

Modify `tailwind.config.ts` to customize Tailwind CSS settings, colors, and plugins.

## 📱 Responsive Design

The application is built with a mobile-first approach and includes responsive breakpoints for:
- Mobile: Default (320px+)
- Tablet: md: (768px+)
- Desktop: lg: (1024px+)
- Large Desktop: xl: (1280px+)

## 🔧 Development

### Adding New Components

1. Create a new component in the appropriate directory
2. Export it from an index file
3. Import and use it in your pages

### Adding New Pages

1. Create a new page component in `src/pages/`
2. Add routing logic in `App.tsx`
3. Update navigation if needed

### Styling Guidelines

- Use Tailwind CSS utility classes
- Follow the component-based styling approach
- Use CSS custom properties for theme values
- Maintain consistent spacing and typography

## 📦 Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions, please open an issue in the repository. 