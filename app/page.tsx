import { getAllDays, getCurrentDay } from "@/lib/content";
import CurrentDay from "@/components/CurrentDay";
import DayCard from "@/components/DayCard";

export default function HomePage() {
  const allDays = getAllDays();
  const currentDay = getCurrentDay();

  // Filter out the current day from the feed
  const pastDays = allDays.filter(day =>
    day.slug !== currentDay?.slug && day.status !== "upcoming"
  );

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero: Latest Post */}
      <section>
        <CurrentDay day={currentDay} />
      </section>

      {/* Previous Posts Feed */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-800">Previous Posts</h2>
          <span className="text-sm text-slate-500">
            {pastDays.length} {pastDays.length === 1 ? "post" : "posts"}
          </span>
        </div>

        {pastDays.length > 0 ? (
          <div className="space-y-3">
            {pastDays.map((day, index) => (
              <DayCard key={day.slug} day={day} index={index} />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500">
            <p className="text-sm">No previous posts yet</p>
          </div>
        )}
      </section>
    </div>
  );
}
