import { getApplicationsBoard } from "@/lib/queries";
import { requireProfile } from "@/lib/profile";
import { KanbanBoard } from "@/components/KanbanBoard";
import { EmptyState, PageHeader } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function ApplicationsPage() {
  const { user, profile } = await requireProfile();
  const cards = await getApplicationsBoard(profile, user.id);

  return (
    <>
      <PageHeader
        title="Applications"
        subtitle={`${cards.length} tracked · move cards through the funnel`}
      />
      {cards.length === 0 ? (
        <EmptyState
          title="No applications tracked yet"
          hint={
            <>
              Open any job and hit <b>Track application</b> — it’ll appear here,
              ready to move through Saved → Applied → Offer.
            </>
          }
        />
      ) : (
        <KanbanBoard cards={cards} />
      )}
    </>
  );
}
