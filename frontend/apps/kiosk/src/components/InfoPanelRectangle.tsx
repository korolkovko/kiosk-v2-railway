// InfoPanelRectangle.tsx
// Rectangular panel component with ASCII-style frames for displaying messages and instructions
// Used for status messages, instructions, and error notifications

import { FunctionComponent } from "react";

export interface InfoPanelRectangleProps {
  message: string;
  type?: 'info' | 'success' | 'error' | 'warning';
  className?: string;
  showIcon?: boolean;
}

const InfoPanelRectangle: FunctionComponent<InfoPanelRectangleProps> = ({
  message,
  type = 'info',
  className = "",
  showIcon = true
}) => {
  
  const getTypeStyles = () => {
    switch (type) {
      case 'success':
        return {
          borderColor: 'border-green-400',
          textColor: 'text-green-400',
          bgColor: 'bg-green-900/20',
          icon: '✓'
        };
      case 'error':
        return {
          borderColor: 'border-red-400',
          textColor: 'text-red-400',
          bgColor: 'bg-red-900/20',
          icon: '✗'
        };
      case 'warning':
        return {
          borderColor: 'border-yellow-400',
          textColor: 'text-yellow-400',
          bgColor: 'bg-yellow-900/20',
          icon: '⚠'
        };
      default: // info
        return {
          borderColor: 'border-[#a7a7a7]',
          textColor: 'text-[#a7a7a7]',
          bgColor: 'bg-gray-900/20',
          icon: 'ℹ'
        };
    }
  };

  const styles = getTypeStyles();

  return (
    <div className={`relative ${className}`}>
      {/* ASCII-style frame */}
      <div className={`
        ${styles.bgColor} 
        ${styles.borderColor} 
        border-2 
        px-8 py-4 
        min-w-[400px] 
        max-w-[800px]
        font-['PT_Sans'] 
        font-mono
      `}>
        
        {/* Top border with corners */}
        <div className={`absolute top-0 left-0 right-0 h-0.5 ${styles.borderColor.replace('border-', 'bg-')}`}>
          <div className={`absolute -top-1 -left-1 w-2 h-2 ${styles.borderColor.replace('border-', 'bg-')} transform rotate-45`}></div>
          <div className={`absolute -top-1 -right-1 w-2 h-2 ${styles.borderColor.replace('border-', 'bg-')} transform rotate-45`}></div>
        </div>
        
        {/* Bottom border with corners */}
        <div className={`absolute bottom-0 left-0 right-0 h-0.5 ${styles.borderColor.replace('border-', 'bg-')}`}>
          <div className={`absolute -bottom-1 -left-1 w-2 h-2 ${styles.borderColor.replace('border-', 'bg-')} transform rotate-45`}></div>
          <div className={`absolute -bottom-1 -right-1 w-2 h-2 ${styles.borderColor.replace('border-', 'bg-')} transform rotate-45`}></div>
        </div>

        {/* Content */}
        <div className="flex items-center justify-center space-x-3">
          {showIcon && (
            <span className={`${styles.textColor} text-2xl font-bold`}>
              {styles.icon}
            </span>
          )}
          <span className={`${styles.textColor} text-xl font-medium text-center leading-relaxed`}>
            {message}
          </span>
        </div>

        {/* ASCII-style decorative elements */}
        <div className={`absolute top-2 left-2 ${styles.textColor} text-xs opacity-50`}>
          ┌─
        </div>
        <div className={`absolute top-2 right-2 ${styles.textColor} text-xs opacity-50`}>
          ─┐
        </div>
        <div className={`absolute bottom-2 left-2 ${styles.textColor} text-xs opacity-50`}>
          └─
        </div>
        <div className={`absolute bottom-2 right-2 ${styles.textColor} text-xs opacity-50`}>
          ─┘
        </div>

      </div>
    </div>
  );
};

export default InfoPanelRectangle;