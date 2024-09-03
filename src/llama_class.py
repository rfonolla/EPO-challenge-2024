import torch
import transformers

class Llama3:
    def __init__(self, model_path, device):
        self.model_id = model_path
        self.device = 'cuda' if device == 'gpu' else 'cpu'
        self.pipeline = transformers.pipeline(
            "text-generation",
            model=self.model_id,
            device=self.device,
            model_kwargs={
                "torch_dtype": torch.float16, #if self.device == 'cuda' else torch.float32, # In float16 or else does not fit in memory. # float16 for gpu
                "low_cpu_mem_usage": True,
            },
        )
        self.terminators = [
            self.pipeline.tokenizer.eos_token_id,
            self.pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>"),
        ]
  
    def get_response(
          self, query, message_history=[], max_tokens=4096, temperature=0.1, top_p=0.9
      ):
        user_prompt = message_history + [{"role": "user", "content": query}]
        prompt = self.pipeline.tokenizer.apply_chat_template(
            user_prompt, tokenize=False, add_generation_prompt=True
        )
        outputs = self.pipeline(
            prompt,
            max_new_tokens=max_tokens,
            eos_token_id=self.terminators,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
        )
        response = outputs[0]["generated_text"][len(prompt):]

        return response, user_prompt + [{"role": "assistant", "content": response}]