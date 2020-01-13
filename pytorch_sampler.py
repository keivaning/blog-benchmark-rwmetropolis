import argparse

import torch
from torch.distributions.normal import Normal


@torch.no_grad()
def rw_metropolis_sampler(logpdf, initial_position):
    """Generate samples using the Random Walk Metropolis algorithm.

    Attributes
    ----------
    logpdf: function
      Returns the log-probability of the model given a position.
    initial_position: np.ndarray, shape (n_dims, n_chains)
      The initial position for each chain.

    Yields
    ------
    np.ndarray (,n_chains)
      The next sample generated by the random walk metropolis algorithm.
    """
    position = initial_position
    log_prob = logpdf(initial_position)
    yield position

    normal_0_1 = Normal(0, 0.1)
    while True:
        move_proposals = normal_0_1.sample(initial_position.shape)
        proposal = position + move_proposals
        proposal_log_prob = logpdf(proposal)

        log_uniform = torch.log(torch.rand(
            initial_position.shape[0], initial_position.shape[1]))
        do_accept = log_uniform < proposal_log_prob - log_prob

        position = torch.where(do_accept, proposal, position)
        log_prob = torch.where(do_accept, proposal_log_prob, log_prob)
        yield position


loc = torch.Tensor([[-2, 0, 3.2, 2.5]]).T
scale = torch.Tensor([[1.2, 1, 5, 2.8]]).T
weights = torch.Tensor([[0.2, 0.3, 0.1, 0.4]]).T
normal_loc_scale = Normal(loc, scale)


@torch.no_grad()
def mixture_logpdf(x):
    """Log probability distribution function of a gaussian mixture model.

    Attribute
    ---------
    x: np.ndarray (4, n_chains)
        Position at which to evaluate the probability density function.

    Returns
    -------
    np.ndarray (, n_chains)
        The value of the log probability density function at x.
    """
    log_probs = normal_loc_scale.log_prob(x)

    return -torch.logsumexp(torch.log(weights) + log_probs, axis=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--samples", default=1000, required=False, type=int, help="Number of samples to take"
    )
    parser.add_argument("--chains", default=4, type=int,
                        help="Number of chains to run")
    args = parser.parse_args()

    n_dims = 4
    n_samples = args.samples
    n_chains = args.chains

    initial_position = torch.zeros((n_dims, n_chains))
    samples = rw_metropolis_sampler(mixture_logpdf, initial_position)
    for i, sample in enumerate(samples):
        if i > n_samples:
            break