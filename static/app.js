const SUPABASE_URL = "BURAYA_PROJECT_URL";
const SUPABASE_ANON_KEY = "BURAYA_ANON_PUBLIC_KEY";

const supabase = supabase.createClient(
  SUPABASE_URL,
  SUPABASE_ANON_KEY
);

async function submitPayment() {
  const email = document.getElementById("email").value;
  const txid = document.getElementById("txid").value;
  const note = document.getElementById("note").value;

  const { error } = await supabase
    .from("payments")
    .insert([{ email, txid, note }]);

  document.getElementById("result").innerText =
    error ? "Hata: " + error.message : "Ödeme bildirimi alındı ✅";
}
