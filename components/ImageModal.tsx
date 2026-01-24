"use client";

import { useEffect } from "react";
import Image from "next/image";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

interface ImageModalProps {
    image: string;
    onClose: () => void;
    onNext: () => void;
    onPrev: () => void;
    currentIndex: number;
    totalImages: number;
}

export default function ImageModal({
    image,
    onClose,
    onNext,
    onPrev,
    currentIndex,
    totalImages,
}: ImageModalProps) {
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
            if (e.key === "ArrowRight") onNext();
            if (e.key === "ArrowLeft") onPrev();
        };

        document.addEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "hidden";

        return () => {
            document.removeEventListener("keydown", handleKeyDown);
            document.body.style.overflow = "unset";
        };
    }, [onClose, onNext, onPrev]);

    return (
        <div className="image-modal-overlay" onClick={onClose}>
            <button className="image-modal-close" onClick={onClose} aria-label="Close">
                <X className="w-6 h-6" />
            </button>

            {totalImages > 1 && (
                <>
                    <button
                        className="image-modal-nav image-modal-prev"
                        onClick={(e) => {
                            e.stopPropagation();
                            onPrev();
                        }}
                        aria-label="Previous image"
                    >
                        <ChevronLeft className="w-8 h-8" />
                    </button>

                    <button
                        className="image-modal-nav image-modal-next"
                        onClick={(e) => {
                            e.stopPropagation();
                            onNext();
                        }}
                        aria-label="Next image"
                    >
                        <ChevronRight className="w-8 h-8" />
                    </button>
                </>
            )}

            <div className="image-modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="image-modal-wrapper">
                    <Image
                        src={image}
                        alt="Full size image"
                        fill
                        sizes="100vw"
                        className="image-modal-image"
                        unoptimized
                    />
                </div>

                <div className="image-modal-counter">
                    {currentIndex + 1} / {totalImages}
                </div>
            </div>
        </div>
    );
}
