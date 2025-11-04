// SmallRoundCountDown.tsx
// Circular countdown component with sector rotation animation and digit display
// Shows countdown from specified duration to 0 with visual progress indicator

import { FunctionComponent, useEffect, useState } from "react";

export interface SmallRoundCountDownProps {
  duration: number; // Duration in seconds
  onComplete?: () => void;
  className?: string;
  size?: number; // Size in pixels
}

const SmallRoundCountDown: FunctionComponent<SmallRoundCountDownProps> = ({
  duration,
  onComplete,
  className = "",
  size = 120
}) => {
  const [timeLeft, setTimeLeft] = useState(duration);
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    if (!isActive || timeLeft <= 0) {
      if (timeLeft <= 0 && onComplete) {
        onComplete();
      }
      return;
    }

    const interval = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          setIsActive(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, timeLeft, onComplete]);

  // Calculate progress percentage (0 to 100)
  const progress = ((duration - timeLeft) / duration) * 100;
  
  // Calculate stroke dash offset for circular progress
  const radius = (size - 8) / 2; // Account for stroke width
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div 
      className={`relative flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
    >
      {/* Background circle */}
      <svg
        className="absolute transform -rotate-90"
        width={size}
        height={size}
      >
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#333"
          strokeWidth="4"
          fill="transparent"
        />
        
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#a7a7a7"
          strokeWidth="4"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-linear"
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          {/* Countdown number */}
          <div className="text-white text-3xl font-bold font-['PT_Sans'] leading-none">
            {timeLeft}
          </div>
          
          {/* Small label */}
          <div className="text-[#a7a7a7] text-xs font-medium mt-1">
            сек
          </div>
        </div>
      </div>

      {/* Outer decorative ring */}
      <div 
        className="absolute border border-[#a7a7a7] rounded-full opacity-30"
        style={{ 
          width: size + 8, 
          height: size + 8,
          top: -4,
          left: -4
        }}
      />

      {/* Inner decorative elements */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div 
          className="border border-[#a7a7a7] rounded-full opacity-20"
          style={{ 
            width: size - 20, 
            height: size - 20 
          }}
        />
      </div>

      {/* Corner accent marks */}
      <div className="absolute top-2 left-2 text-[#a7a7a7] text-xs opacity-50">
        ╭
      </div>
      <div className="absolute top-2 right-2 text-[#a7a7a7] text-xs opacity-50">
        ╮
      </div>
      <div className="absolute bottom-2 left-2 text-[#a7a7a7] text-xs opacity-50">
        ╰
      </div>
      <div className="absolute bottom-2 right-2 text-[#a7a7a7] text-xs opacity-50">
        ╯
      </div>

    </div>
  );
};

export default SmallRoundCountDown;