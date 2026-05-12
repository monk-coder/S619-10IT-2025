use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;

#[derive(Serialize, Deserialize, Clone)]
struct BPESerialized {
    vocab: HashMap<u32, String>,
    merges: Vec<(u32, u32)>,
    next_id: u32,
    is_whitespace: Vec<bool>,
}

#[derive(Clone)]
struct BPETokenizer {
    vocab: HashMap<u32, String>,
    merges: Vec<(u32, u32)>,
    next_id: u32,
    is_whitespace: Vec<bool>,
    char_to_id: HashMap<char, u32>,
    merge_to_id: HashMap<(u32, u32), u32>,
}

impl BPETokenizer {
    pub fn new() -> Self {
        Self {
            vocab: HashMap::new(),
            merges: Vec::new(),
            next_id: 0,
            is_whitespace: Vec::new(),
            char_to_id: HashMap::new(),
            merge_to_id: HashMap::new(),
        }
    }

    pub fn init_vocab(&mut self, corpus: &[String]) {
        let mut chars: Vec<char> = corpus
            .iter()
            .flat_map(|s| s.chars())
            .collect::<std::collections::HashSet<_>>()
            .into_iter()
            .collect();
        chars.sort();
        for c in chars {
            let id = self.next_id;
            self.vocab.insert(id, c.to_string());
            self.char_to_id.insert(c, id);
            self.is_whitespace.push(c.is_whitespace());
            self.next_id += 1;
        }
    }

    pub fn train(&mut self, corpus: &[String], num_merges: usize) {
        let mut tokens_list: Vec<Vec<u32>> = corpus
            .iter()
            .map(|s| s.chars().map(|c| self.char_to_id[&c]).collect())
            .collect();

        for _ in 0..num_merges {
            let mut pairs: HashMap<(u32, u32), usize> = HashMap::new();
            for tokens in &tokens_list {
                for i in 0..tokens.len().saturating_sub(1) {
                    let a = tokens[i];
                    let b = tokens[i + 1];
                    if !self.is_whitespace[a as usize] && !self.is_whitespace[b as usize] {
                        *pairs.entry((a, b)).or_insert(0) += 1;
                    }
                }
            }
            if pairs.is_empty() {
                break;
            }

            let (&best_pair, _) = pairs.iter().max_by_key(|&(_, c)| c).unwrap();
            let new_id = self.next_id;
            self.next_id += 1;

            self.vocab.insert(
                new_id,
                format!("{}{}", self.vocab[&best_pair.0], self.vocab[&best_pair.1]),
            );
            self.merges.push(best_pair);
            self.merge_to_id.insert(best_pair, new_id);
            self.is_whitespace.push(false);

            for tokens in &mut tokens_list {
                let mut next = Vec::with_capacity(tokens.len());
                let mut i = 0;
                while i < tokens.len() {
                    if i + 1 < tokens.len()
                        && tokens[i] == best_pair.0
                        && tokens[i + 1] == best_pair.1
                    {
                        next.push(new_id);
                        i += 2;
                    } else {
                        next.push(tokens[i]);
                        i += 1;
                    }
                }
                *tokens = next;
            }
        }
    }

    pub fn encode(&self, text: &str) -> Vec<u32> {
        let mut tokens: Vec<u32> = text.chars().map(|c| self.char_to_id[&c]).collect();
        for &(a, b) in &self.merges {
            let new_id = self.merge_to_id[&(a, b)];
            let mut next = Vec::with_capacity(tokens.len());
            let mut i = 0;
            while i < tokens.len() {
                if i + 1 < tokens.len() && tokens[i] == a && tokens[i + 1] == b {
                    next.push(new_id);
                    i += 2;
                } else {
                    next.push(tokens[i]);
                    i += 1;
                }
            }
            tokens = next;
        }
        tokens
    }

    pub fn decode(&self, ids: &[u32]) -> String {
        ids.iter()
            .map(|&id| self.vocab.get(&id).cloned().unwrap_or_default())
            .collect()
    }

    pub fn save(&self, path: &str) {
        let data = BPESerialized {
            vocab: self.vocab.clone(),
            merges: self.merges.clone(),
            next_id: self.next_id,
            is_whitespace: self.is_whitespace.clone(),
        };
        fs::write(path, serde_json::to_string(&data).unwrap()).unwrap();
    }

    pub fn load(path: &str) -> Self {
        let data: BPESerialized = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        let mut char_to_id = HashMap::new();
        let mut merge_to_id = HashMap::new();

        for (&id, s) in &data.vocab {
            if s.chars().count() == 1 {
                char_to_id.insert(s.chars().next().unwrap(), id);
            }
        }

        let initial_size = data.next_id - data.merges.len() as u32;
        for (i, &pair) in data.merges.iter().enumerate() {
            merge_to_id.insert(pair, initial_size + i as u32);
        }

        Self {
            vocab: data.vocab,
            merges: data.merges,
            next_id: data.next_id,
            is_whitespace: data.is_whitespace,
            char_to_id,
            merge_to_id,
        }
    }
}

fn main() {
    let data = fs::read_to_string("data.txt").expect("data.txt not found");
    let lines: Vec<String> = data.lines().map(String::from).collect();
    let split = lines.len() * 80 / 100;
    let (train, val) = (&lines[..split], &lines[split..]);

    let mut base = BPETokenizer::new();
    base.init_vocab(&lines);

    println!(
        "{:<12} | {:<10} | {:<15} | {:<12}",
        "merges", "vocab_size", "avg_len", "top1_len"
    );
    println!("{}", "-".repeat(55));

    for m in [0, 2000, 8000] {
        let mut tok = base.clone();
        tok.train(train, m);

        let mut total = 0;
        let mut lens = Vec::with_capacity(val.len());
        for s in val {
            let ids = tok.encode(s);
            total += ids.len();
            lens.push(ids.len());
        }
        lens.sort_unstable();
        let top1 = lens.get(lens.len() * 99 / 100).copied().unwrap_or(0);
        let avg = total as f64 / val.len() as f64;
        println!(
            "{:<12} | {:<10} | {:<15.2} | {:<12}",
            m,
            tok.vocab.len(),
            avg,
            top1
        );
        tok.save("bpe_merges.json");
    }

    println!("\n=== AUTO-CHECK: decode(encode(x)) == x ===");
    let tok = BPETokenizer::load("bpe_merges.json");
    let mut passed = 0;
    for s in val {
        if tok.decode(&tok.encode(s)) == *s {
            passed += 1;
        }
    }
    let status = if passed == val.len() {
        "PASSED"
    } else {
        "FAILED"
    };
    println!(
        "{}/{} strings checked. RESULT: {}",
        passed,
        val.len(),
        status
    );
}
