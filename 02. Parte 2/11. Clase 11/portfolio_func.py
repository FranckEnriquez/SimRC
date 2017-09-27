
def get_historical_closes(ticker, start_date, end_date):
    import pandas_datareader.data as web
    p = web.DataReader(ticker, "yahoo", start_date, end_date).sort_index('major_axis')
    d = p.to_frame()['Adj Close'].reset_index()
    d.rename(columns={'minor': 'Ticker', 'Adj Close': 'Close'}, inplace=True)
    pivoted = d.pivot(index='Date', columns='Ticker')
    pivoted.columns = pivoted.columns.droplevel(0)
    return pivoted

def sim_mont_portfolio(daily_returns,num_portfolios,risk_free):
    num_assets=len(daily_returns.T)
    #Packages
    import pandas as pd
    import sklearn.covariance as skcov
    import numpy as np
    import statsmodels.api as sm
    huber = sm.robust.scale.Huber()
    #Mean and standar deviation returns
    returns_av, scale = huber(daily_returns)
    #returns_av = daily_returns.mean()
    covariance= skcov.ShrunkCovariance().fit(daily_returns).covariance_
    #Simulated weights
    weights = np.array(np.random.random(num_assets*num_portfolios)).reshape(num_portfolios,num_assets)
    weights = weights*np.matlib.repmat(1/weights.sum(axis=1),num_assets,1).T
    ret=252*weights.dot(returns_av).T
    sd = np.zeros(num_portfolios)
    for i in range(num_portfolios):
        sd[i]=np.sqrt(252*(((weights[i,:]).dot(covariance)).dot(weights[i,:].T))) 
    sharpe=np.divide((ret-risk_free),sd)    
    return pd.DataFrame(data=np.column_stack((ret,sd,sharpe,weights)),columns=(['Returns','SD','Sharpe']+list(daily_returns.columns)))

def calc_daily_returns(closes):
    import numpy as np
    return np.log(closes/closes.shift(1))[1:]

def optimal_portfolio(daily_returns,N):
    # Frontier points
    #Packages
    import pandas as pd
    import sklearn.covariance as skcov
    import numpy as np
    import cvxopt as opt
    from cvxopt import blas, solvers
    import statsmodels.api as sm
    huber = sm.robust.scale.Huber()
    n = len(daily_returns.T)
    daily_returns = np.asmatrix(daily_returns)
    mus = [10**(5.0 * t/N - 1.0) for t in range(N)]    
    #cvxopt matrices
    S = opt.matrix(skcov.ShrunkCovariance().fit(daily_returns).covariance_)
    returns_av, scale = huber(daily_returns)
    pbar = opt.matrix(returns_av)    
    # Constraint matrices
    G = -opt.matrix(np.eye(n))   # negative n x n identity matrix
    h = opt.matrix(0.0, (n ,1))
    A = opt.matrix(1.0, (1, n))
    b = opt.matrix(1.0)    
    # Calculate efficient frontier weights using quadratic programming
    portfolios = [solvers.qp(mu*S, -pbar, G, h, A, b)['x'] for mu in mus]
    ## Risk and returns
    returns = [252*blas.dot(pbar, x) for x in portfolios]
    risks = [np.sqrt(252*blas.dot(x, S*x)) for x in portfolios]
    return  portfolios, returns, risks