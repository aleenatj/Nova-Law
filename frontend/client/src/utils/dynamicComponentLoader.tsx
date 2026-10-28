import React from "react";

interface DataItem {
  type: string;
  version?: number;
  [key: string]: any;
}

interface DynamicComponentLoaderProps {
  item: DataItem;
  components: Record<string, React.ComponentType<any>>;
  fallbackComponent?: React.ComponentType<any>;
  loadingComponent?: React.ComponentType<any>;
  errorComponent?: React.ComponentType<any>;
}

export function DynamicComponentLoader({ 
  item, 
  components, 
  fallbackComponent,
  loadingComponent,
  errorComponent 
}: DynamicComponentLoaderProps) {
  const Component = components[item.type];
  
  if (!Component) {
    if (fallbackComponent) {
      const FallbackComponent = fallbackComponent;
      return <FallbackComponent data={item} />;
    }
    
    if (errorComponent) {
      const ErrorComponent = errorComponent;
      return <ErrorComponent data={item} />;
    }
    
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <p className="text-gray-500">
          Unknown type: {item.type}
        </p>
      </div>
    );
  }

  return <Component data={item} />;
}

// Utility function to create component mappings
export function createComponentMap<T extends Record<string, React.ComponentType<any>>>(
  components: T
): T {
  return components;
}

// Higher-order component for lazy loading
export function withLazyLoading<P extends { data: DataItem }>(
  Component: React.ComponentType<P>,
  LoadingComponent?: React.ComponentType
) {
  return function LazyLoadedComponent(props: P) {
    const [isLoading, setIsLoading] = React.useState(true);
    
    React.useEffect(() => {
      setIsLoading(false);
    }, []);
    
    if (isLoading && LoadingComponent) {
      return <LoadingComponent />;
    }
    
    return <Component {...props} />;
  };
}

