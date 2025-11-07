/**
 * Simple placeholder dashboard component
 */
export default function Dashboard() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-card p-6 rounded-lg border">
          <h3 className="text-sm font-medium text-muted-foreground">Total Revenue</h3>
          <p className="text-2xl font-bold mt-2">$0.00</p>
        </div>
        <div className="bg-card p-6 rounded-lg border">
          <h3 className="text-sm font-medium text-muted-foreground">Total Expenses</h3>
          <p className="text-2xl font-bold mt-2">$0.00</p>
        </div>
        <div className="bg-card p-6 rounded-lg border">
          <h3 className="text-sm font-medium text-muted-foreground">Net Cash Flow</h3>
          <p className="text-2xl font-bold mt-2">$0.00</p>
        </div>
        <div className="bg-card p-6 rounded-lg border">
          <h3 className="text-sm font-medium text-muted-foreground">Runway</h3>
          <p className="text-2xl font-bold mt-2">-- days</p>
        </div>
      </div>
      <div className="mt-8 bg-card p-6 rounded-lg border">
        <h2 className="text-xl font-semibold mb-4">AI Financial Summary</h2>
        <p className="text-muted-foreground">Connect a data source to generate AI insights.</p>
      </div>
    </div>
  )
}
