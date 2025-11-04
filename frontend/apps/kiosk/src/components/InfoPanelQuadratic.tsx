// InfoPanelQuadratic.tsx
// Square panel component with ASCII-style frames for displaying pickup codes and QR codes
// Used for showing pickup number, pin code, and potentially QR codes

import { FunctionComponent } from "react";

export interface InfoPanelQuadraticProps {
  pickupNumber?: string;
  pinCode?: string;
  qrCode?: string;
  className?: string;
  title?: string;
}

const InfoPanelQuadratic: FunctionComponent<InfoPanelQuadraticProps> = ({
  pickupNumber,
  pinCode,
  qrCode,
  className = "",
  title = "КОД ПОЛУЧЕНИЯ"
}) => {

  return (
    <div className={`relative ${className}`}>
      {/* ASCII-style square frame */}
      <div className="
        bg-gray-900/30 
        border-2 
        border-[#a7a7a7] 
        w-[300px] 
        h-[300px] 
        flex 
        flex-col 
        items-center 
        justify-center 
        font-['PT_Sans'] 
        font-mono
        relative
      ">
        
        {/* Corner decorations */}
        <div className="absolute top-2 left-2 text-[#a7a7a7] text-sm opacity-70">
          ╔═
        </div>
        <div className="absolute top-2 right-2 text-[#a7a7a7] text-sm opacity-70">
          ═╗
        </div>
        <div className="absolute bottom-2 left-2 text-[#a7a7a7] text-sm opacity-70">
          ╚═
        </div>
        <div className="absolute bottom-2 right-2 text-[#a7a7a7] text-sm opacity-70">
          ═╝
        </div>

        {/* Content */}
        <div className="flex flex-col items-center justify-center space-y-4 text-center">
          
          {/* Title */}
          <div className="text-[#a7a7a7] text-lg font-bold mb-2">
            {title}
          </div>

          {/* QR Code placeholder (if provided) */}
          {qrCode && (
            <div className="w-24 h-24 border-2 border-[#a7a7a7] flex items-center justify-center mb-4">
              <div className="text-[#a7a7a7] text-xs text-center">
                QR<br/>CODE
              </div>
            </div>
          )}

          {/* Pickup Number */}
          {pickupNumber && (
            <div className="flex flex-col items-center space-y-1">
              <div className="text-[#a7a7a7] text-sm font-medium">
                НОМЕР:
              </div>
              <div className="text-white text-3xl font-bold tracking-wider">
                {pickupNumber}
              </div>
            </div>
          )}

          {/* PIN Code */}
          {pinCode && (
            <div className="flex flex-col items-center space-y-1">
              <div className="text-[#a7a7a7] text-sm font-medium">
                ПИН-КОД:
              </div>
              <div className="text-white text-2xl font-bold tracking-widest">
                {pinCode}
              </div>
            </div>
          )}

          {/* Decorative separator */}
          <div className="w-full flex justify-center mt-4">
            <div className="text-[#a7a7a7] text-xs opacity-50">
              ═══════════════
            </div>
          </div>

        </div>

        {/* Border accent lines */}
        <div className="absolute top-0 left-1/4 w-1/2 h-0.5 bg-[#a7a7a7] opacity-30"></div>
        <div className="absolute bottom-0 left-1/4 w-1/2 h-0.5 bg-[#a7a7a7] opacity-30"></div>
        <div className="absolute left-0 top-1/4 w-0.5 h-1/2 bg-[#a7a7a7] opacity-30"></div>
        <div className="absolute right-0 top-1/4 w-0.5 h-1/2 bg-[#a7a7a7] opacity-30"></div>

      </div>
    </div>
  );
};

export default InfoPanelQuadratic;