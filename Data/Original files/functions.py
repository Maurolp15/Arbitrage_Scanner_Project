from tqdm import tqdm
from web3 import Web3
import web3
import os
import time
import pprint
from tokens import init_dict_token_dex
from oraclefeed import Orfeed
from dotenv import load_dotenv

load_dotenv()


def getTokenToTokenPrice(orfeed_i, tokenSrc, tokenDst, dex, amount_src_token=1):

    res = orfeed_i.getExchangeRate(tokenSrc, tokenDst, dex, amount_src_token)

    return {
        "tokenSrc": tokenSrc,
        "tokenDst": tokenDst,
        "tokenPair": tokenSrc + "-" + tokenDst,
        "provider": dex,
        "price": res,
    }


def simple_getTokenToTokenPrice(
    orfeed_i, src_token, src_token_infos, dst_token, dst_token_infos
):

    result = {}
    providers_list = ["UNISWAPBYSYMBOLV2", "KYBERBYSYMBOLV1"]
    tmp_res = {}
    for provider in providers_list:
        buy = getTokenToTokenPrice(
            orfeed_i,
            src_token,
            dst_token,
            provider,
            amount_src_token=10 ** src_token_infos["decimals"],
        )
        sell = getTokenToTokenPrice(
            orfeed_i, dst_token, src_token, provider, amount_src_token=buy["price"]
        )
        tmp_res[provider] = {
            "buy_price_wei": buy["price"] / (10 ** dst_token_infos["decimals"]),
            "sell_price_wei": sell["price"]
            * buy["price"]
            / (10 ** (dst_token_infos["decimals"] + src_token_infos["decimals"])),
        }
        if buy["price"] > 0 and sell["price"] > 0:
            tmp_res[provider] = {
                "buy_price_wei": buy["price"] / (10 ** dst_token_infos["decimals"]),
                "sell_price_wei": sell["price"]
                * buy["price"]
                / (10 ** (dst_token_infos["decimals"] + src_token_infos["decimals"])),
            }
        else:
            return None
        result[provider] = tmp_res[provider]
    return result
