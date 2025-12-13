const SUPABASE_URL = "https://yfkoekysmmrfvwgrgpay.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlma29la3lzbW1yZnZ3Z3JncGF5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU2MTIxOTIsImV4cCI6MjA4MTE4ODE5Mn0.QM7numW8JFELkJK0rJrxkuIz0Ky7VdkpnE0vkrSehOE";

const supabase = window.supabase.createClient(
  SUPABASE_URL,
  SUPABASE_ANON_KEY
);

async function submitPayment() {
  const email = document.getElementById("email").value;
  const txid = document.getElementById("txid").value;
  const note = document.getElementById("note").value;

  const resultEl = document.getElementById("result");

  if (!email || !txid) {
    resultEl.innerText = "E-posta ve TxID zorunludur.";
    return;
  }

  const { error } = await supabase
    .from("payments")
    .insert([{ email, txid, note }]);

  resultEl.innerText = error
    ? "Hata: " + error.message
    : "Ödeme bildirimi alındı ✅";
}
