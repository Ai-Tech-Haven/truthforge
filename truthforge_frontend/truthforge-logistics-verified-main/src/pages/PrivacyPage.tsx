const PrivacyPage = () => (
  <div className="max-w-3xl mx-auto space-y-8 py-4">
    <div>
      <h2 className="text-2xl font-heading font-black text-foreground mb-2">Privacy Policy</h2>
      <p className="text-xs text-muted-foreground">Effective: January 1, 2026</p>
    </div>

    {[
      {
        title: "1. Information We Collect",
        body: "TruthForge collects shipment data, cargo manifests, and document hashes submitted through the platform. We do not collect personally identifiable information beyond what is required for trade compliance and verification purposes.",
      },
      {
        title: "2. How We Use Your Data",
        body: "Data submitted to TruthForge is used solely to perform pre-arrival verification, issue port trust receipts, and anchor immutable audit records to the Hedera Consensus Service (HCS). We do not sell or share your data with third parties outside of the verification workflow.",
      },
      {
        title: "3. Hedera Consensus Service",
        body: "Verification events are anchored as immutable records on the Hedera public ledger. Once submitted, these records cannot be altered or deleted. Only cryptographic hashes and structured metadata are written on-chain — raw document content is never stored on the ledger.",
      },
      {
        title: "4. Data Retention",
        body: "Shipment records and verification logs are retained for a minimum of 7 years to comply with international trade regulations. You may request a copy of your data by contacting our support team.",
      },
      {
        title: "5. Security",
        body: "All data in transit is encrypted via TLS 1.3. Access to backend systems is restricted by API key authentication and role-based access controls. We conduct regular security reviews of our infrastructure.",
      },
      {
        title: "6. Contact",
        body: "For privacy-related inquiries, contact us at privacy@truthforge.io.",
      },
    ].map(({ title, body }) => (
      <section key={title} className="rounded-xl border border-border bg-card p-6 shadow-card">
        <h3 className="text-sm font-heading font-bold text-foreground mb-3">{title}</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">{body}</p>
      </section>
    ))}
  </div>
);

export default PrivacyPage;
