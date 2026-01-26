import fs from "fs";
import path from "path";
import ImageGallery from "@/components/ImageGallery";

export const metadata = {
    title: "Sunflower | The Workshop",
    description: "Visual resources and diagrams from the security workshop",
};

interface ImageMetadata {
    filename: string;
    name: string;
}

export default function SunflowerPage() {
    // Read images from public/gallery directory
    const galleryPath = path.join(process.cwd(), "public", "gallery");
    const metadataPath = path.join(galleryPath, "metadata.json");
    let images: { src: string; name: string }[] = [];

    try {
        if (fs.existsSync(galleryPath)) {
            const files = fs.readdirSync(galleryPath);
            let metadata: ImageMetadata[] = [];

            // Load metadata if exists
            if (fs.existsSync(metadataPath)) {
                const metadataContent = fs.readFileSync(metadataPath, "utf-8");
                metadata = JSON.parse(metadataContent);
            }

            images = files
                .filter((file) => /\.(jpg|jpeg|png|webp|gif)$/i.test(file))
                .map((file) => {
                    const meta = metadata.find((m) => m.filename === file);
                    return {
                        src: `/the-workshop/gallery/${file}`,
                        name: meta?.name || file,
                    };
                });
        }
    } catch (error) {
        console.error("Error reading gallery directory:", error);
    }

    return (
        <div className="max-w-7xl mx-auto px-6 py-12">
            <div className="mb-12">
                <h1 className="text-4xl font-bold text-slate-900 mb-3">Sunflower 🌻</h1>
                <p className="text-lg text-slate-600">
                    Visual resources, diagrams, and reference materials from the workshop
                </p>
            </div>

            <ImageGallery images={images} />
        </div>
    );
}
