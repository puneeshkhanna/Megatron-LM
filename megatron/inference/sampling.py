# coding=utf-8
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities sampling.
Part of this code is inspired by:
 - https://github.com/ari-holtzman/degen/blob/master/gen.py
 - https://huggingface.co/transformers/_modules/transformers/generation_logits_process.html
"""


import torch



def modify_logits_for_top_k_filtering(logits, top_k):
    """Set the logits for none top-k values to -inf."""

    filter_ = logits < torch.topk(logits, top_k)[0][..., -1, None]
    logits.masked_fill_(filter_, float('-Inf'))



def modify_logits_for_top_p_filtering(logits, top_p):
    """Set the logits for none top-p values to -inf."""

    # First sort and calculate cumulative sum of probabilities.
    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
    cumulative_probs = sorted_logits.softmax(dim=-1).cumsum(dim=-1)

    # Filteration based on the cumulative sum.
    filter_ = cumulative_probs > top_p
    # This shift by 1 is weird and I cannot justify it. This existed
    # in the original implementation:
    #   https://github.com/ari-holtzman/degen/blob/master/gen.py
    # and I guess it is needed so keeping it for now.
    filter_[:, 1:] = filter_[:, :-1].clone()
    # Make sure we at least have one token to select from.
    filter_[..., 0] = 0

    # Fill in the filtered part
    filter_ = filter_.scatter(1, sorted_indices, filter_)
    logits.masked_fill_(filter_, float('-Inf'))



def sample_and_update_logits(logits, greedy=False, top_k=0, top_p=0.0,
                             temperature=1.0, vocab_size=None):
    """ Sample and update the logits and generate a token.
    Note: logits has the dimension [b, v] where b is the batch size
          and v is the vocabulary size.
    Note: logits are modifed in place so the sampling modification
          are reflected in the original full logits.
    If vocab_size is provided, we will make sure the sample that is
    generated is in [0, vocab-size). This will avoid out of vocabulary
    generations due to padding.
    """

    # Check logits for consistency.
    assert logits.ndim == 2, 'expected the logits to be of [b, v] shape.'
    assert logits.is_contiguous(), 'input logits should be contiguous.'
    assert logits.type() == 'torch.cuda.FloatTensor', \
        'input logits should be floats.'

    # Greedy is just simple argmax.
    if greedy:
        assert top_k == 0, 'cannot set both greedy and top-k samplings.'
        assert top_p == 0.0, 'cannot set both greedy and top-p samplings.'
        samples = torch.argmax(logits, dim=-1)

    # Top-k or top-p sampling.
    else:
        # Apply temperature in place.
        logits.div_(temperature)

        if top_k > 0:
            assert top_p == 0.0, 'cannot set both top-k and top-p samplings.'
            assert top_k <= logits.size(1), 'top-k is larger than logit size.'
            if vocab_size:
                assert top_k < vocab_size, 'top-k is larger than vocab size.'
            modify_logits_for_top_k_filtering(logits, top_k)

        elif top_p > 0.0:
            assert top_p <= 1.0, 'top-p should be in (0, 1].'
            modify_logits_for_top_p_filtering(logits, top_p)

        # After filtering, we need to recalculate the distribution.
        probs = logits.softmax(dim=-1)
        samples = torch.multinomial(probs, num_samples=1).view(-1)

    # If vocab size is provided, make sure the samples are in
    # in the range [0, vocab-size).
    if vocab_size:
        samples = torch.clamp(samples, min=0, max=(vocab_size - 1))

    return samples
