// src/components/common/LoadingSpinner.tsx
import { Loader2 } from 'lucide-react';

const LoadingSpinner = () => (
  <div className="flex justify-center items-center h-full">
    <Loader2 className="h-12 w-12 animate-spin text-primary" />
  </div>
);

export default LoadingSpinner;