import { useEffect, useState } from 'react';
import truthforgeLogo from '@/assets/truthforge-logo.png';

interface SplashScreenProps {
  onLoadingComplete: () => void;
  minDisplayTime?: number;
}

const SplashScreen = ({ onLoadingComplete, minDisplayTime = 2000 }: SplashScreenProps) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onLoadingComplete, 500); // Wait for fade-out animation
    }, minDisplayTime);

    return () => clearTimeout(timer);
  }, [onLoadingComplete, minDisplayTime]);

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-hero transition-opacity duration-500 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
    >
      <div className="flex flex-col items-center justify-center space-y-6">
        {/* Logo with zoom-out animation */}
        <div className="animate-zoom-out-splash">
          <img
            src={truthforgeLogo}
            alt="TruthForge"
            className="w-48 h-48 md:w-64 md:h-64 object-contain drop-shadow-2xl"
          />
        </div>

        {/* Loading text with fade-in animation */}
        <div className="animate-fade-in-up">
          <p className="text-teal text-sm md:text-base font-medium tracking-wide">
            Initializing Verification Network...
          </p>
          
          {/* Loading dots animation */}
          <div className="flex justify-center space-x-1 mt-4">
            <div className="w-2 h-2 bg-teal rounded-full animate-bounce-dot" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-teal rounded-full animate-bounce-dot" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-teal rounded-full animate-bounce-dot" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SplashScreen;
