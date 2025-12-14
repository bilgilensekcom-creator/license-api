const SUPABASE_URL = "https://yfkoekysmmrfvwgrgpay.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlma29la3lzbW1yZnZ3Z3JncGF5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU2MTIxOTIsImV4cCI6MjA4MTE4ODE5Mn0.QM7numW8JFELkJK0rJrxkuIz0Ky7VdkpnE0vkrSehOE";

const supabase = window.supabase.createClient(
  SUPABASE_URL,
  SUPABASE_ANON_KEY
);

async function submitPayment() {
  const email = document.getElementById("email").value.trim();
  const txid = document.getElementById("txid").value.trim();
  const network = document.getElementById("network").value;
  const note = document.getElementById("note").value.trim();

  if (!email || !txid || !network) {
    document.getElementById("result").innerText =
      "E-posta, TxID ve gönderim ağı zorunludur.";
    return;
  }

  const { error } = await supabase
    .from("payments")
    .insert([{
      email: email,
      txid: txid,
      network: network,
      note: note,
      status: "pending"
    }]);

  document.getElementById("result").innerText =
    error
      ? "Hata: " + error.message
      : "Ödeme bildirimi alındı ✅";
}
