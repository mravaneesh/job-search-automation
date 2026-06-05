import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
} from "@react-pdf/renderer";
import type { ResumeData } from "@/lib/resume";

const ACCENT = "#4f46e5";
const INK = "#1f2937";
const MUTED = "#6b7280";
const LINE = "#e5e7eb";

const s = StyleSheet.create({
  page: {
    paddingTop: 40,
    paddingBottom: 44,
    paddingHorizontal: 44,
    fontFamily: "Helvetica",
    fontSize: 10,
    color: INK,
    lineHeight: 1.4,
  },
  name: { fontSize: 22, fontFamily: "Helvetica-Bold", color: INK },
  contact: { fontSize: 9.5, color: MUTED, marginTop: 3 },
  target: { fontSize: 10, color: ACCENT, marginTop: 6, fontFamily: "Helvetica-Bold" },
  rule: { borderBottomWidth: 2, borderBottomColor: ACCENT, marginTop: 10, marginBottom: 14 },
  section: { marginBottom: 14 },
  heading: {
    fontSize: 10,
    fontFamily: "Helvetica-Bold",
    color: ACCENT,
    letterSpacing: 1.2,
    marginBottom: 6,
    textTransform: "uppercase",
  },
  body: { fontSize: 10, color: INK },
  skillRow: { flexDirection: "row", flexWrap: "wrap" },
  pill: {
    fontSize: 9,
    borderWidth: 1,
    borderColor: LINE,
    borderRadius: 3,
    paddingVertical: 2,
    paddingHorizontal: 5,
    marginRight: 5,
    marginBottom: 5,
    color: INK,
  },
  pillRelevant: {
    fontSize: 9,
    fontFamily: "Helvetica-Bold",
    backgroundColor: "#eef2ff",
    borderWidth: 1,
    borderColor: "#c7d2fe",
    color: ACCENT,
    borderRadius: 3,
    paddingVertical: 2,
    paddingHorizontal: 5,
    marginRight: 5,
    marginBottom: 5,
  },
  para: { fontSize: 9.5, color: INK, marginBottom: 6 },
  label: { fontSize: 9, color: MUTED, marginBottom: 3 },
  footer: {
    position: "absolute",
    bottom: 22,
    left: 44,
    right: 44,
    fontSize: 8,
    color: MUTED,
    textAlign: "center",
    borderTopWidth: 1,
    borderTopColor: LINE,
    paddingTop: 6,
  },
});

export function ResumeDocument({ data }: { data: ResumeData }) {
  const contactBits = [data.email, data.location].filter(Boolean).join("   •   ");

  return (
    <Document
      title={`Resume — ${data.name} — ${data.company}`}
      author={data.name}
    >
      <Page size="A4" style={s.page}>
        <Text style={s.name}>{data.name}</Text>
        {contactBits ? <Text style={s.contact}>{contactBits}</Text> : null}
        <Text style={s.target}>
          Targeting: {data.jobTitle} · {data.company}
          {data.matchScore != null ? `   (match ${data.matchScore})` : ""}
        </Text>
        <View style={s.rule} />

        <View style={s.section}>
          <Text style={s.heading}>Summary</Text>
          <Text style={s.body}>{data.summary}</Text>
        </View>

        <View style={s.section}>
          <Text style={s.heading}>Core Skills</Text>
          {data.relevantSkills.length > 0 && (
            <>
              <Text style={s.label}>Matched to this role</Text>
              <View style={s.skillRow}>
                {data.relevantSkills.map((sk) => (
                  <Text key={sk} style={s.pillRelevant}>
                    {sk}
                  </Text>
                ))}
              </View>
            </>
          )}
          {data.otherSkills.length > 0 && (
            <>
              <Text style={[s.label, { marginTop: 4 }]}>Additional</Text>
              <View style={s.skillRow}>
                {data.otherSkills.map((sk) => (
                  <Text key={sk} style={s.pill}>
                    {sk}
                  </Text>
                ))}
              </View>
            </>
          )}
        </View>

        <View style={s.section}>
          <Text style={s.heading}>Experience</Text>
          {data.experienceParagraphs.length > 0 ? (
            data.experienceParagraphs.map((p, i) => (
              <Text key={i} style={s.para}>
                {p}
              </Text>
            ))
          ) : (
            <Text style={[s.body, { color: MUTED }]}>
              Upload a résumé in your profile to populate this section from your
              real experience.
            </Text>
          )}
        </View>

        {data.missingSkills.length > 0 && (
          <View style={s.section}>
            <Text style={s.heading}>Worth Addressing</Text>
            <Text style={[s.body, { color: MUTED }]}>
              Skills this posting mentions that aren&apos;t on your profile:{" "}
              {data.missingSkills.join(", ")}.
            </Text>
          </View>
        )}

        <Text style={s.footer} fixed>
          Draft résumé tailored for {data.company} · generated {data.generatedOn} ·
          review before sending
        </Text>
      </Page>
    </Document>
  );
}
