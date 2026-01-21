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
    <div className="animate-fade-in">
      {/* Hero: Latest Post */}
      <CurrentDay day={currentDay} />

      {/* Previous Posts Feed */}
      {pastDays.length > 0 && (
        <section className="mt-20 pt-10 border-t border-slate-100">
          <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-10">Previous Entries</h2>
          <div>
            {pastDays.map((day, index) => (
              <DayCard key={day.slug} day={day} index={index} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
