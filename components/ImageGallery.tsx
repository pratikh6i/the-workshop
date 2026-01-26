"use client";

import { useState } from "react";
import Image from "next/image";
import ImageModal from "./ImageModal";

interface ImageGalleryProps {
    images: { src: string; name: string }[];
}

export default function ImageGallery({ images }: ImageGalleryProps) {
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [selectedIndex, setSelectedIndex] = useState<number>(0);

    const openModal = (image: string, index: number) => {
        setSelectedImage(image);
        setSelectedIndex(index);
    };

    const closeModal = () => {
        setSelectedImage(null);
    };

    const navigateImage = (direction: "prev" | "next") => {
        const newIndex =
            direction === "next"
                ? (selectedIndex + 1) % images.length
                : (selectedIndex - 1 + images.length) % images.length;
        setSelectedIndex(newIndex);
        setSelectedImage(images[newIndex].src);
    };

    if (images.length === 0) {
        return (
            <div className="text-center py-20">
                <p className="text-slate-500 text-lg">
                    No images yet. Add images to <code className="px-2 py-1 bg-slate-100 rounded">public/gallery/</code>
                </p>
            </div>
        );
    }

    return (
        <>
            <div className="gallery-grid">
                {images.map((image, index) => (
                    <div
                        key={image.src}
                        className="gallery-item"
                        onClick={() => openModal(image.src, index)}
                    >
                        <div className="gallery-image-wrapper">
                            <Image
                                src={image.src}
                                alt={image.name}
                                fill
                                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                                className="gallery-image"
                                unoptimized
                            />
                        </div>
                        <div className="mt-2 text-center text-sm text-slate-600 font-medium">
                            {image.name}
                        </div>
                    </div>
                ))}
            </div>

            {selectedImage && (
                <ImageModal
                    image={selectedImage}
                    onClose={closeModal}
                    onNext={() => navigateImage("next")}
                    onPrev={() => navigateImage("prev")}
                    currentIndex={selectedIndex}
                    totalImages={images.length}
                />
            )}
        </>
    );
}
