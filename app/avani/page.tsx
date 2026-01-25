export const metadata = {
    title: "Hi Avani! | The Workshop",
    description: "A special message",
};

export default function AvaniPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
            <div className="text-center px-6">
                <h1 className="text-8xl font-bold mb-4 bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 bg-clip-text text-transparent animate-pulse">
                    Hi Avani! 👋
                </h1>
                <p className="text-2xl text-slate-600 mt-6">
                    Welcome to The Workshop 💜
                </p>
            </div>
        </div>
    );
}
