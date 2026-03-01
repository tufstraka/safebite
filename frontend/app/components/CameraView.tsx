'use client';

import { useEffect, useRef, useState } from 'react';
import { Camera, X } from 'lucide-react';

interface CameraViewProps {
  onCapture: (file: File) => void;
  onClose: () => void;
}

export default function CameraView({ onCapture, onClose }: CameraViewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);

  useEffect(() => {
    startCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startCamera = async () => {
    try {
      // Check if mediaDevices is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setError('camera not supported on this device. use upload instead.');
        return;
      }

      // Try to get camera access
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: { ideal: 'environment' }, // Prefer back camera but don't require it
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      });
      
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err: any) {
      console.error('Camera error:', err);
      
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setPermissionDenied(true);
        setError('camera permission denied. tap allow when your browser asks, or use upload instead.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('no camera found on this device. use upload instead.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setError('camera is being used by another app. close other apps and try again, or use upload.');
      } else {
        setError('camera not available. try upload instead.');
      }
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;

    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0);
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], `snap-${Date.now()}.jpg`, { type: 'image/jpeg' });
          onCapture(file);
          if (stream) {
            stream.getTracks().forEach(track => track.stop());
          }
        }
      }, 'image/jpeg', 0.95);
    }
  };

  if (error) {
    return (
      <div className="fixed inset-0 bg-slate-900 flex flex-col items-center justify-center z-50 p-6">
        <div className="text-center max-w-md">
          <Camera className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <p className="text-white text-lg mb-2">{error}</p>
          {permissionDenied && (
            <p className="text-slate-400 text-sm mb-6">
              you might need to enable camera in your browser settings
            </p>
          )}
          <button
            onClick={onClose}
            className="px-8 py-3 bg-emerald-500 text-white rounded-full font-bold hover:bg-emerald-600 transition-colors"
          >
            got it
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black z-50">
      {/* Camera view */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Top bar */}
      <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-center z-10">
        <button
          onClick={onClose}
          className="w-10 h-10 bg-black/50 backdrop-blur-sm rounded-full flex items-center justify-center"
        >
          <X className="w-6 h-6 text-white" />
        </button>
        <p className="text-white text-sm font-medium bg-black/50 backdrop-blur-sm px-4 py-2 rounded-full">
          snap your menu
        </p>
        <div className="w-10" />
      </div>

      {/* Capture button - Snapchat style */}
      <div className="absolute bottom-8 left-0 right-0 flex justify-center z-10">
        <button
          onClick={capturePhoto}
          className="w-20 h-20 rounded-full border-4 border-white bg-white/20 backdrop-blur-sm active:scale-95 transition-transform"
        >
          <div className="w-16 h-16 rounded-full bg-white mx-auto" />
        </button>
      </div>
    </div>
  );
}
