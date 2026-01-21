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
      {/* Hero: Current Active Day */}
      <section>
        <CurrentDay day={currentDay} />
      </section>

      {/* Past Days Feed */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-slate-800">
            Previous Days
          </h2>
          <span className="text-sm text-slate-500">
            {pastDays.length} {pastDays.length === 1 ? "entry" : "entries"}
          </span>
        </div>

        {pastDays.length > 0 ? (
          <div className="space-y-4">
            {pastDays.map((day, index) => (
              <DayCard key={day.slug} day={day} index={index} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-slate-500">
            <p className="text-lg mb-2">No previous entries yet</p>
            <p className="text-sm">Complete your first day to see it here</p>
          </div>
        )}
      </section>
    </div>
  );
}
